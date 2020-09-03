from manager.consumer import ContinuousConsumer


def notification(username, msg=''):
	ContinuousConsumer.send_notification(username, msg)
