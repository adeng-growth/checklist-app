def handler(request):
    return {
        "statusCode": 200,
        "headers": {"Content-Type": "application/json"},
        "body": "{\"status\":\"ok\",\"source\":\"test.py\"}"
    }