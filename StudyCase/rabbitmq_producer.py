import pika, sys

#建立到Rabbitmq的连接
credentials = pika.PlainCredentials("guest","guest")
conn_para = pika.ConnectionParameters("localhost",credentials=credentials)
conn_broker = pika.BlockingConnection(conn_para)

#获得信道
channel = conn_broker.channel()

#声明交换器
channel.exchange_declare(exchange="hello-exchange",type="direct",passive=False,durable=True,auto_delete=False)

#创建纯文本消息
msg = sys.argv[1]
msg_props = pika.BasicProperties()
msg_props.content_type = "text/plain"

#发布消息
channel.basic_publish(body=msg,exchange="hello-exchange",properties=msg_props,routing_key="hola")
