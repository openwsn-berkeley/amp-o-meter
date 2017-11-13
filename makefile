deploy:
	scp calibrator.py amp_o_meter.py run.sh pi@rp2.local:~/amp-o-meter/


runrp2:
	scp calibrator.py amp_o_meter.py run.sh pi@rp2.local:~/amp-o-meter/
	ssh -t pi@rp2.local 'python3 amp-o-meter/calibrator.py'


get_results:
	scp  pi@rp2.local:~/Desktop/history/* ./history/
