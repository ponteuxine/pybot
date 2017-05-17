import config
import telebot
import time
import eventlet
import requests
import logging
from time import sleep

URL_VK = config.vk_url
FILENAME_VK = 'last_known_id.txt'
BASE_OF_POST_URL = config.base_of_post
SINGLE_RUN = config.single_run
BOT_TOKEN = config.token
CHANNEL_NAME = config.channel_name
TIME_LONG_SLEEP = config.time_long_sleep
TIME_SHORT_SLEEP = config.time_short_sleep
MIN_LIKES = config.min_likes

bot = telebot.TeleBot(config.token)

def get_data():
	timeout = eventlet.Timeout(10)
	try:
		feed = requests.get(URL_VK)
		return feed.json()
	except eventlet.timeout.Timeout:
		logging.warning('Vk made a timeout while I was retrieving data from it\'s API. Cancelling. ')
		return None
	finally:
		timeout.cancel()

def send_new_posts(items, last_id):
	for item in items:
		if item['id'] <= last_id:
			break
		# if item['likes'] is not None:
		# 	if item['likes'] < MIN_LIKES:
		# 		break
		link = '{!s}{!s}'.format(BASE_OF_POST_URL, item['id'])
		bot.send_message(CHANNEL_NAME, link)

		#sleep for second to avoid errors
		time.sleep(TIME_SHORT_SLEEP)
	return

def check_new_posts_vk():
	#Write current start time
	logging.info('[VK] Start of scanning for new posts. ')
	with open(FILENAME_VK, 'rt') as file:
		last_id = int(file.read())
		if last_id is None:
			logging.error('Could not read from storage; skipped iteration. ')
			return
		logging.info('Last id of post in VK = {!s}'.format(last_id))
	try: 
		feed = get_data()
		# If there was a timeout before, miss the iteration.
		# If everything is OK - parse the posts
		if feed is not None:
			entries = feed['response'][1:] 
			# start parsing from the second elem, because the first one is unknown number
			try:
				# If the post is pinned, miss it
				tmp = entries[0]['is_pinned']
				# Start sending messages
				send_new_posts(entries[1:], last_id)
			except KeyError:
				send_new_posts(entries, last_id)
			# Write the new last_id into file
			with open(FILENAME_VK, 'wt') as file:
				try:
					tmp = entries[0]['is_pinned']
					# If the first post was pinned, save ID of the second post
					file.write(str(entries[1]['id']))
					logging.info('New last_id of VK post is {!s}'.format((entries[1]['id'])))
				except KeyError:
					file.write(str(entries[0]['id']))
					logging.info('New last_id of VK post is {!s}'.format((entries[1]['id'])))

	except Exception as ex:
		logging.error('Exception of type {!s} in check_new_post(): {!s}'.format(type(ex).__name__, str(ex)))
		pass
		logging.info('[VK] Finished scanning')
		return


if __name__ == '__main__':
    logging.getLogger('requests').setLevel(logging.CRITICAL)

    logging.basicConfig(format='[%(asctime)s] %(filename)s:%(lineno)d %(levelname)s - %(message)s', level=logging.INFO, filename='bot_log.log', datefmt='%d.%m.%Y %H:%M:%S')
    if not SINGLE_RUN:
    	while True:
    		check_new_posts_vk()
    		# 4 min pause before repeat scan
    		logging.info('[App] Script went to sleep. ')
    		time.sleep(TIME_LONG_SLEEP)
    else:
    	check_new_posts_vk()
    logging.info('[App] Script exited.\n')