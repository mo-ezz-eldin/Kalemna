# Serving Qwen 2.5 10B on Modal with vLLM — Thinking Framework

> **Rules**: This document gives you **frameworks for thinking**, not copy-paste answers. Every section tells you **what to calculate**, **what questions to ask yourself**, and **what tradeoffs to evaluate**.

---

## 1. The Budget Constraint: Staying Under $5 on Modal

### How Modal Pricing Works — What You Need to Understand

Modal charges for **three things**. You need to understand each one before you write a single line of code:

| Cost Dimension | What Eats Your Money | Questions to Ask Yourself |
|---------------|---------------------|--------------------------|
| **GPU time** | Every second the GPU is allocated to your container, whether it's doing inference or sitting idle | What GPU tier do I need for a 10B model? How long will my container stay warm? What's the per-second cost? |
| **CPU/Memory time** | Container overhead (CPU, RAM) while running | How much system RAM does vLLM need beyond GPU VRAM? |
| **Cold start** | Loading the model from disk into GPU VRAM each time a container spins up | How large is the model in GB? How long does loading take? Can I avoid cold starts? |

### The Math You Must Do Before Deploying

Before touching Modal, sit down and calculate these:

**Step 1: Model Size in VRAM**
- A 10B parameter model at FP16 = `10B × 2 bytes` = **~20 GB** just for weights
- At FP32 = `10B × 4 bytes` = **~40 GB** (you can't afford this)
- At INT4 (4-bit quantization) = `10B × 0.5 bytes` = **~5 GB** for weights
- But weights are NOT the only thing in VRAM. What else lives there? (KV cache, activations, vLLM overhead — see Section 3)

**Step 2: Which GPU Fits?**
- Think about what GPU tiers Modal offers. Research their GPU options and pricing per second/hour.
- What's the cheapest GPU that can hold your model + KV cache + overhead?
- **Key insight**: Choosing the wrong GPU tier is how you blow your $5 in minutes. A bigger GPU costs more per second. A too-small GPU won't load the model at all.

**Step 3: Estimate Total GPU-Seconds**
```
Total cost = GPU_price_per_second × total_seconds_running
```
- If the GPU costs $X/hour, you get `$5 / $X` hours total
- Ask yourself: How many requests do I need to serve? How long does each inference take? Am I paying for idle time between requests?

**Step 4: The Cold Start Tax**
- Every time your container starts from scratch, the model loads from disk → CPU RAM → GPU VRAM
- For a 10B model, this can take 30-120 seconds
- During cold start, **you're paying for the GPU but serving zero requests**
- How many cold starts can you afford within $5?

### Strategies to Investigate (Not Solutions — Think About These)

- **Container lifecycle management**: Modal has mechanisms to keep containers warm for a window after the last request. What is this feature called? What are the tradeoffs between warm time and cost?
- **Quantization to shrink the GPU requirement**: Can you use a smaller (cheaper) GPU by quantizing the model? What's the quality tradeoff? (See Section 4)
- **Batch requests**: If you send 5 requests during one warm window vs 5 separate cold starts, how much do you save?
- **Pre-downloading model weights**: Where does vLLM download model weights from? Can you bake them into a Modal image to avoid download time during cold start?

> [!IMPORTANT]
> **The single biggest budget mistake**: Leaving a container running with `keep_warm=1` indefinitely. A warm GPU at $X/hour will drain $5 in hours. Calculate exactly how many warm-hours your budget allows.

---

## 2. Cost Per User — The Universal Framework

This framework applies whether you're on Modal, RunPod, AWS, your own GPU, or any provider.

### The Formula

```
Cost per user request = Compute Cost + Memory Cost + Storage Cost + Network Cost
```

For LLM inference specifically:

```
Cost per request = (GPU_cost_per_second × inference_time_seconds) 
                 + (cold_start_cost_amortized_over_N_requests)
                 + (egress_cost_per_MB × response_size_MB)
```

### Breaking Down Compute Cost

**For API providers** (OpenAI, Google, Anthropic):
```
Cost = (input_tokens × input_price_per_token) + (output_tokens × output_price_per_token)
```
Simple. They give you the price per million tokens.

**For self-hosted LLMs** (this is YOUR case — much harder to calculate):

You need to understand that the cost isn't per-token — it's **per-second of GPU time**. But you CAN derive a per-token cost:

```
Effective cost per token = GPU_cost_per_second / throughput_tokens_per_second
```

This means your **throughput directly determines your cost**. Two identical GPUs running the same model, but one with optimized batching, will have different costs per token.

#### How to Measure Your Throughput

You need these numbers for YOUR specific setup:
1. **Prefill throughput**: tokens/second during the prompt processing phase
2. **Decode throughput**: tokens/second during generation
3. **Time to First Token (TTFT)**: latency before the first output token appears
4. **Total inference time**: for a typical request (your judge prompt ~500 tokens input, ~200 tokens output)

```
Example calculation (you must plug in YOUR numbers):
- GPU costs $0.80/hour = $0.000222/second
- Your system processes 50 tokens/second during decode
- A typical response is 150 tokens
- Decode time = 150/50 = 3 seconds
- Prefill time for 500 input tokens = ~0.5 seconds
- Total inference = 3.5 seconds
- Cost per request = $0.000222 × 3.5 = $0.000778
- Compare to Gemini API: 500 input + 150 output tokens at API rates
```

### How to Compare Providers — Build This Table

| Provider | GPU Type | GPU $/hr | Your Model's tok/s | Cost per Request | Cold Start? | Min Billing |
|----------|----------|----------|--------------------|-----------------:|-------------|-------------|
| Modal | ? | ? | ? | ? | Yes | per-second |
| RunPod | ? | ? | ? | ? | Serverless option | per-second |
| Vast.ai | ? | ? | ? | ? | Persistent | per-hour |
| Your own GPU | Your card | Electricity only | ? | ? | No | None |
| Gemini API | N/A | N/A | N/A | token-based | No | per-request |

> [!TIP]
> The key insight: Self-hosted is cheaper **only at scale**. If you serve 10 requests/day, API is cheaper. If you serve 10,000 requests/day, self-hosted wins. Find YOUR crossover point.

---

## 3. KV Cache — The Most Important Thing You Don't Fully Understand Yet

### What Is the KV Cache and Why Does It Exist?

During autoregressive generation, a transformer generates tokens **one at a time**. At each step, the model needs to attend to ALL previous tokens. Without caching, you'd recompute attention over the entire sequence at every step:

```
Step 1: Compute attention for [token_1] → output token_2
Step 2: Compute attention for [token_1, token_2] → output token_3
Step 3: Compute attention for [token_1, token_2, token_3] → output token_4
...
```

This is O(n²) in sequence length — catastrophically expensive.

**The KV cache stores the Key and Value projections** from previous tokens so you only compute the NEW token's Q, K, V and attend against the cached K, V from all previous tokens:

```
Step 1: Compute K₁, V₁ for token_1. Store in cache. Generate token_2.
Step 2: Compute K₂, V₂ for token_2. Store in cache. Attend Q₂ against [K₁,K₂], [V₁,V₂]. Generate token_3.
Step 3: Compute K₃, V₃ for token_3. Store in cache. Attend Q₃ against [K₁,K₂,K₃], [V₁,V₂,V₃]. Generate token_4.
```

Now each step is O(n) instead of O(n²). The KV cache **trades memory for compute**.

### How to Calculate KV Cache Size

This is critical for understanding whether your model fits on a GPU and how many concurrent requests you can serve.

```
KV cache size per token = 2 × num_layers × num_kv_heads × head_dim × precision_bytes
```

Let's break this down for Qwen 2.5 (you need to look up the exact architecture):

| Parameter | What to Research | Why It Matters |
|-----------|-----------------|----------------|
| `num_layers` | How many transformer layers does Qwen 2.5 10B have? | More layers = more cache per token |
| `num_kv_heads` | Does it use Multi-Head Attention (MHA) or Grouped-Query Attention (GQA)? How many KV heads? | GQA has FEWER KV heads than query heads — this is a huge memory saving. Research what GQA is and why modern models use it. |
| `head_dim` | What is the dimension of each attention head? | Usually `hidden_size / num_attention_heads` |
| `precision_bytes` | FP16 = 2 bytes, FP32 = 4 bytes, INT8 = 1 byte | Lower precision = smaller cache but potential quality loss |

**Example calculation** (plug in Qwen 2.5 10B's actual values):
```
If: num_layers=48, num_kv_heads=8 (GQA), head_dim=128, FP16 (2 bytes)
KV per token = 2 × 48 × 8 × 128 × 2 = 196,608 bytes ≈ 192 KB per token

For a 2048-token sequence:
KV cache = 192 KB × 2048 = 384 MB per request

For 4 concurrent requests:
KV cache = 384 MB × 4 = 1.5 GB
```

### Why This Matters for Your Budget

```
Total GPU VRAM needed = Model Weights + KV Cache + Activations + Framework Overhead

If your GPU has 24 GB VRAM:
  Model weights (INT4) = ~5 GB
  Framework overhead   = ~2 GB
  Available for KV     = ~17 GB
  
  Max concurrent requests = 17 GB / KV_per_request
```

**This is how you determine**:
1. Whether the model fits on a given GPU at all
2. How many concurrent users you can serve
3. Whether you need quantization for the model weights to free VRAM for KV cache

> [!WARNING]
> If you don't calculate KV cache size, you'll hit OOM (Out of Memory) errors in production with no understanding of why. The model loads fine with 1 user but crashes with 3.

### KV Cache Optimization Techniques to Research

| Technique | What It Does | What to Investigate |
|-----------|-------------|---------------------|
| **PagedAttention** | Manages KV cache like virtual memory pages — no fragmentation | This is vLLM's core innovation. How does it prevent wasted VRAM from internal fragmentation? |
| **Prefix Caching** | Shares KV cache of common prompt prefixes across requests | Your judge prompt is ~500 tokens and IDENTICAL every request. Those 500 tokens' KV values are recomputed every time. What if they were cached? |
| **KV Cache Quantization** | Store KV cache in INT8 or FP8 instead of FP16 | Halves KV memory → doubles concurrent capacity. What quality impact? |
| **Sliding Window Attention** | Only caches the last N tokens, not the entire history | Does Qwen 2.5 use this? What's the window size? |

> [!IMPORTANT]
> **For your Kalemna system specifically**: Your judge prompt is ~500 tokens that are identical for every request. With prefix caching, those 500 tokens' KV cache is computed ONCE and shared across all requests. This means:
> - First request: compute KV for 500 static + N dynamic tokens
> - Subsequent requests: reuse 500 cached + compute only N dynamic tokens
> - This is DIRECTLY relevant to TASK-7.1 in your production_missing file

---

## 4. Memory Bottlenecks — Where Your VRAM Goes

### The VRAM Budget Breakdown

Think of GPU VRAM as a fixed-size budget:

```
┌─────────────────────────────────────────────┐
│                 Total VRAM                   │
│                                              │
│  ┌──────────────────────┐                    │
│  │   Model Weights      │ ← Fixed cost       │
│  │   (largest chunk)    │    Determined by     │
│  │                      │    model size +      │
│  │                      │    quantization      │
│  └──────────────────────┘                    │
│  ┌──────────────────────┐                    │
│  │   KV Cache           │ ← Variable cost     │
│  │   (grows with        │    Grows with        │
│  │    sequence length    │    # concurrent      │
│  │    × batch size)     │    requests          │
│  └──────────────────────┘                    │
│  ┌──────────┐                                │
│  │ Activations│ ← Temporary                   │
│  │ (forward   │   During computation          │
│  │  pass)     │   Freed after each layer      │
│  └──────────┘                                │
│  ┌──────────┐                                │
│  │ Framework │ ← Fixed overhead               │
│  │ Overhead  │   CUDA context, vLLM           │
│  │ (~1-2 GB) │   internals, buffers          │
│  └──────────┘                                │
└─────────────────────────────────────────────┘
```

### How to Calculate Each Component

**Model Weights:**
```
FP32:  params × 4 bytes
FP16:  params × 2 bytes
INT8:  params × 1 byte
INT4:  params × 0.5 bytes
NF4:   params × 0.5 bytes (bitsandbytes uses this)
```

**KV Cache** (calculated in Section 3 above)

**Activations** (during forward pass):
```
Activation memory per layer ≈ batch_size × seq_len × hidden_size × precision_bytes
```
- These are temporary — each layer's activations are freed after the layer completes
- In inference (no gradient), this is relatively small
- During prefill (processing the full prompt), this peaks because `seq_len` is the full prompt length
- During decode (generating tokens), `seq_len = 1` for the new token, so this is tiny

### The Decision Framework: Quantization vs GPU Size

You have two knobs to make the model fit:

```
Option A: Bigger GPU (more VRAM, higher $/hr)
  → Model fits comfortably
  → More room for KV cache (more concurrent users)
  → Higher cost per second

Option B: Smaller quantization (less VRAM, same GPU)
  → Model weights shrink
  → More room for KV cache (more concurrent users)
  → Potential quality degradation
  → Lower cost per second (cheaper GPU)
```

**The question you must answer**: For YOUR use case (Arabic customer support), how much quality can you sacrifice? This requires evaluation (TASK-4.1 from your production_missing).

| Quantization Level | Weight Size | Quality Impact | What to Research |
|-------------------|-------------|---------------|------------------|
| FP16 | 20 GB | Baseline | Does it even fit on your target GPU? |
| INT8 (W8A8) | 10 GB | Minimal (~1% quality loss typically) | GPTQ-INT8 vs bitsandbytes INT8 |
| INT4 (W4A16) | 5 GB | Moderate (1-3% quality loss) | AWQ vs GPTQ vs bitsandbytes NF4. Which does vLLM support? |
| GGUF Q4_K_M | ~5-6 GB | Moderate | This is llama.cpp format — does vLLM support it? |

---

## 5. Compute Bottlenecks — Why Your Inference Is Slow

### The Two Phases of LLM Inference

This is the most important concept for understanding and optimizing performance:

```
┌─────────────────────────────────────────────────────────┐
│                    PREFILL PHASE                         │
│  Process the ENTIRE input prompt at once                │
│                                                          │
│  Input: [token₁, token₂, ..., tokenₙ]                  │
│  Nature: COMPUTE-BOUND (lots of matrix multiplications) │
│  Bottleneck: GPU compute (FLOPS)                        │
│  Parallelizable: YES (all input tokens processed        │
│                   simultaneously)                        │
│  Time: proportional to prompt length                    │
│  This phase determines TTFT (Time to First Token)       │
└─────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────┐
│                    DECODE PHASE                          │
│  Generate tokens ONE AT A TIME                          │
│                                                          │
│  Each step: generate 1 token using KV cache             │
│  Nature: MEMORY-BOUND (reading weights + KV cache       │
│          from VRAM, doing very little compute per byte) │
│  Bottleneck: GPU memory bandwidth (GB/s)                │
│  Parallelizable: NO (each token depends on previous)    │
│  Time: proportional to output length                    │
│  This phase determines generation speed (tok/s)         │
└─────────────────────────────────────────────────────────┘
```

### Why This Matters — Compute-Bound vs Memory-Bound

**Prefill is compute-bound:**
- You're doing massive matrix multiplications over the entire prompt
- The GPU's TFLOPS (compute power) is the bottleneck
- More powerful GPU = faster prefill
- Batching helps: processing 4 prompts at once barely takes longer than 1

**Decode is memory-bound:**
- For each generated token, you read ALL model weights from VRAM through the GPU once
- You also read the entire KV cache
- The GPU does very little compute relative to the bytes it reads
- The bottleneck is **memory bandwidth** (how fast the GPU can read from VRAM)
- A GPU with 900 GB/s bandwidth will decode ~2× faster than one with 450 GB/s, regardless of compute power

### The Arithmetic Intensity Concept

```
Arithmetic Intensity = FLOPs / Bytes Accessed

Prefill: High arithmetic intensity (many FLOPs per byte) → compute-bound
Decode:  Low arithmetic intensity (few FLOPs per byte)  → memory-bound
```

**Why you care**: This tells you what to optimize:
- If prefill is your bottleneck → you need more compute (better GPU) or a shorter prompt
- If decode is your bottleneck → you need more memory bandwidth or smaller model (quantization reduces bytes read per token)

### How to Calculate Theoretical Decode Speed

```
Theoretical max tokens/second = Memory Bandwidth (bytes/s) / Model Size (bytes)

Example:
- GPU bandwidth: 900 GB/s (A100)
- Model size in FP16: 20 GB
- Theoretical max: 900/20 = 45 tokens/second (per request, no batching)

With INT4 quantization:
- Model size: 5 GB
- Theoretical max: 900/5 = 180 tokens/second
```

**Reality is lower** due to: KV cache reads, framework overhead, memory access patterns. Expect 50-70% of theoretical.

> [!TIP]
> This is why quantization is SO important for decode speed: smaller model = fewer bytes to read per token = more tokens per second. It's not just about fitting in memory — it directly improves generation speed.

---

## 6. Performance Optimization Checklist — Questions to Ask Yourself

### Before Deployment

- [ ] What is the model's architecture? (layers, heads, KV heads, hidden dim)
- [ ] What is the minimum VRAM required at my chosen quantization?
- [ ] How much VRAM is left for KV cache after loading weights?
- [ ] How many concurrent requests can I serve given KV cache constraints?
- [ ] What is the theoretical decode throughput on my target GPU?

### Serving Engine Configuration (vLLM specific)

Research what each of these vLLM parameters does and how they affect performance:

| Parameter | What It Controls | Impact |
|-----------|-----------------|--------|
| `max_model_len` | Maximum sequence length (input + output) | Directly affects max KV cache size. Lower = more concurrent requests but shorter conversations |
| `gpu_memory_utilization` | Fraction of GPU memory vLLM can use | Higher = more KV cache space = more concurrent requests. But leaves no room for spikes → OOM |
| `max_num_seqs` | Maximum concurrent requests in a batch | Caps concurrency. What happens if this is too low? Too high? |
| `quantization` | Which quantization format to use | AWQ, GPTQ, bitsandbytes — which does vLLM support best? |
| `enable_prefix_caching` | Whether to cache KV for common prefixes | DIRECTLY relevant to your static judge/finalize prompts |
| `tensor_parallel_size` | Split model across multiple GPUs | Only if you have multiple GPUs |
| `dtype` | Data type for computation | float16 vs bfloat16 — does your target GPU support bfloat16? |

### The Optimization Priority Order

1. **Make it work** — Model loads, responds correctly
2. **Make it fit** — Quantize if needed to fit on cheaper GPU
3. **Make it fast** — Enable prefix caching, tune batch sizes
4. **Make it cheap** — Minimize idle GPU time, optimize container lifecycle
5. **Make it measurable** — Log TTFT, decode speed, cost per request

---

## 7. Putting It All Together — Your Decision Framework

### Decision Tree (Not a Solution — A Framework)

```
START: I want to serve Qwen 2.5 10B on Modal under $5
  │
  ├─ Q1: At FP16, the model is ~20 GB. What's the cheapest Modal GPU with ≥24 GB VRAM?
  │    └─ Research Modal's GPU tiers and prices
  │
  ├─ Q2: Can I quantize to fit on a smaller/cheaper GPU?
  │    └─ INT4 = ~5 GB weights. What GPU has ≥16 GB VRAM (5 GB weights + KV + overhead)?
  │    └─ Is the quality acceptable for Arabic customer support? You MUST test this.
  │
  ├─ Q3: How many total GPU-seconds does my $5 budget give me?
  │    └─ $5 / (GPU_price_per_hour / 3600)
  │
  ├─ Q4: How many of those seconds are "wasted" on cold starts?
  │    └─ Model load time × number of container spin-ups
  │    └─ Can I minimize cold starts? (pre-baked images, warm pools)
  │
  ├─ Q5: How many actual inference requests can I serve?
  │    └─ (Total GPU-seconds - cold start seconds) / avg_inference_seconds
  │
  └─ Q6: Is this enough for my use case?
       └─ Development/demo? Maybe 50-100 requests is fine.
       └─ Production? You need a different approach (persistent GPU, not serverless).
```

### The Key Tradeoffs to Navigate

| Tradeoff | Option A | Option B | How to Decide |
|----------|----------|----------|---------------|
| GPU size | Bigger (fits easily, more expensive) | Smaller + quantization (tight fit, cheaper) | Calculate: does the per-second savings outweigh the quality loss? |
| Container lifecycle | Keep warm (fast response, burns budget) | Cold start per request (slow, conserves budget) | How latency-sensitive is your use case? |
| Quantization level | FP16 (best quality) | INT4 (4× smaller) | Run your evaluation dataset at both levels. What's the quality delta? |
| max_model_len | Long (supports long conversations) | Short (more concurrent capacity) | What's the actual max conversation length in your system? Your prompts + history + response |

---

## 8. What to Research Next — Ordered by Priority

1. **Modal GPU pricing page** — What GPUs are available? What's the per-second cost? Is there a free tier or credits?
2. **Qwen 2.5 10B model card** — Architecture details (layers, heads, KV heads, GQA?)
3. **vLLM documentation on quantization** — Which formats are supported? AWQ? GPTQ? How to specify?
4. **Modal examples for vLLM** — Modal likely has example code for serving LLMs. Study it but don't copy blindly.
5. **vLLM prefix caching docs** — How to enable it, what it saves
6. **Memory bandwidth of your target GPU** — This determines your decode speed ceiling

> [!CAUTION]
> **Do NOT deploy to Modal before doing the math on paper first.** Every minute of trial-and-error with a running GPU costs real money. Calculate everything offline, then deploy with confidence.

---

## Quick Reference Formulas

```python
# Model weight memory
weight_memory_bytes = num_params * bytes_per_param  # FP16=2, INT8=1, INT4=0.5

# KV cache per token
kv_per_token = 2 * num_layers * num_kv_heads * head_dim * precision_bytes

# KV cache per request
kv_per_request = kv_per_token * max_sequence_length

# Max concurrent requests
max_concurrent = (total_vram - weight_memory - overhead) / kv_per_request

# Theoretical decode speed
max_tok_per_sec = gpu_memory_bandwidth_bytes_per_sec / weight_memory_bytes

# Cost per request
cost_per_request = gpu_cost_per_second * total_inference_seconds

# Cost per token (self-hosted)
cost_per_token = gpu_cost_per_second / measured_tokens_per_second

# Break-even vs API
# If API costs $X per 1M tokens and self-hosted costs $Y per GPU-hour:
# Break-even at: Y / (throughput_tokens_per_hour × X / 1_000_000) hours of utilization
```
