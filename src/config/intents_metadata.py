Meta_Data_Intents={
  "place_order": {
    "required_metadata": ["items", "delivery_address"]
  },
  "get_invoice": {
    "required_metadata": ["order_id"]
  },
  "track_order": {
    "required_metadata": ["order_id"]
  },
  "get_refund": {
    "required_metadata": ["order_id", "refund_reason"]
  },
  "contact_customer_service": {
    "required_metadata": []
  },
  "delivery_options": {
    "required_metadata": ["city_or_region"]
  },
  "complaint": {
    "required_metadata": ["complaint_details"]
  },
  "change_shipping_address": {
    "required_metadata": ["order_id", "new_address"]
  },
  "check_cancellation_fee": {
    "required_metadata": []
  },
  "track_refund": {
    "required_metadata": ["refund_id_or_order_id"]
  },
  "delivery_period": {
    "required_metadata": []
  },
  "check_refund_policy": {
    "required_metadata": []
  },
  "change_order": {
    "required_metadata": ["order_id", "items_to_add_or_remove"]
  },
  "cancel_order": {
    "required_metadata": ["order_id", "cancellation_reason"]
  },
  "review": {
    "required_metadata": ["rating", "feedback_text"]
  }
}