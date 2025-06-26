import boto3

# DynamoDB クライアント作成（ローカル用）
dynamodb = boto3.client(
    'dynamodb',
    endpoint_url='http://localhost:8001',
    region_name='ap-northeast-1',
    aws_access_key_id='fakeMyKeyId',
    aws_secret_access_key='fakeSecretAccessKey'
)

def create_tables():
    # QAitem テーブル
    dynamodb.create_table(
        TableName='QAitem',
        KeySchema=[
            {'AttributeName': 'id', 'KeyType': 'HASH'},
            {'AttributeName': 'qa_id', 'KeyType': 'RANGE'}
        ],
        AttributeDefinitions=[
            {'AttributeName': 'id', 'AttributeType': 'S'},        # ← ここを "S" に変更
            {'AttributeName': 'qa_id', 'AttributeType': 'N'}
        ],
        BillingMode='PAY_PER_REQUEST'
    )

    # QAinfo テーブル
    dynamodb.create_table(
        TableName='QAinfo',
        KeySchema=[
            {'AttributeName': 'id', 'KeyType': 'HASH'}
        ],
        AttributeDefinitions=[
            {'AttributeName': 'id', 'AttributeType': 'S'}         # ← ここを "S" に変更
        ],
        BillingMode='PAY_PER_REQUEST'
    )

    # QAresult テーブル（変更なしでOK）
    dynamodb.create_table(
        TableName='QAresult',
        KeySchema=[
            {'AttributeName': 'id_qaid', 'KeyType': 'HASH'},
            {'AttributeName': 'u_id', 'KeyType': 'RANGE'}
        ],
        AttributeDefinitions=[
            {'AttributeName': 'id_qaid', 'AttributeType': 'S'},
            {'AttributeName': 'u_id', 'AttributeType': 'S'}
        ],
        BillingMode='PAY_PER_REQUEST'
    )

if __name__ == "__main__":
    create_tables()
    print("Tables created successfully.")
