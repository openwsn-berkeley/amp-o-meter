deploy:
	scp amp-o-meter.py run.sh pi@rp2.local:~/amp-o-meter/

get_results:
	scp  pi@rp2.local:~/Desktop/history/* ./history/
