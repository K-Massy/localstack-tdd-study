import json


class OrderWorker:
    def __init__(self, sqs_client, queue_url: str):
        """コンストラクタ（PHPの __construct に相当）"""
        self.sqs_client = sqs_client
        self.queue_url = queue_url

    def process_next_order(self) -> dict | None:
        # 1. SQSキューからメッセージを最大1件受信する
        response = self.sqs_client.receive_message(
            QueueUrl=self.queue_url,
            MaxNumberOfMessages=1,
        )

        # メッセージが空（キューに何もない）場合は None を返す
        messages = response.get("Messages", [])
        if not messages:
            return None

        message = messages[0]

        try:
            # 2. 受信したメッセージの本文（JSON文字列）を辞書型に変換する
            order_data = json.loads(message["Body"])

            # 3. 税込合計金額を計算する（小数点以下は切り捨て）
            subtotal = order_data["price"] * order_data["quantity"]
            total_amount = int(subtotal * 1.1)

        except (json.JSONDecodeError, KeyError):
            # 不正なJSONや項目不足の場合は、メッセージを削除せずに安全に終了する
            return None

        # 4. 処理が正常に完了したので、二重処理を防ぐためにSQSからメッセージを削除する
        self.sqs_client.delete_message(
            QueueUrl=self.queue_url,
            ReceiptHandle=message["ReceiptHandle"],
        )

        return {
            "order_id": order_data["order_id"],
            "total_amount": total_amount,
        }