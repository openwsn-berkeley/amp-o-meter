deploy:
	scp amp-o-meter.py run.sh pi@raspberrypi.local:~/Desktop

get_results:
	scp  pi@raspberrypi.local:~/Desktop/history/* ./history/
