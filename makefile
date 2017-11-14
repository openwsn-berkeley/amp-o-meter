deploy:
	scp calibrator.py amp_o_meter.py makefile run.sh pi@rp2.local:~/amp-o-meter/


runrp2:
	scp calibrator.py amp_o_meter.py run.sh pi@rp2.local:~/amp-o-meter/
	ssh -t pi@rp2.local 'python3 amp-o-meter/calibrator.py'


get_results:
	scp  pi@rp2.local:~/Desktop/history/* ./history/


s1:
	ssh -t pi@rp2.local 'cd amp-o-meter; python3 amp_o_meter.py --csv off --ui_type terminal --int_pin 21'


s2:
	ssh -t pi@rp2.local 'cd amp-o-meter; python3 amp_o_meter.py --csv off --ui_type terminal --int_pin 20'


s3:
	ssh -t pi@rp2.local 'cd amp-o-meter; python3 amp_o_meter.py --csv off --ui_type terminal --int_pin 16'


s4:
	ssh -t pi@rp2.local 'cd amp-o-meter; python3 amp_o_meter.py --csv off --ui_type terminal --int_pin 12'


s5:
	ssh -t pi@rp2.local 'cd amp-o-meter; python3 amp_o_meter.py --csv off --ui_type terminal --int_pin 25'


s6:
	ssh -t pi@rp2.local 'cd amp-o-meter; python3 amp_o_meter.py --csv off --ui_type terminal --int_pin 24'


s7:
	ssh -t pi@rp2.local 'cd amp-o-meter; python3 amp_o_meter.py --csv off --ui_type terminal --int_pin 23'


s8:
	ssh -t pi@rp2.local 'cd amp-o-meter; python3 amp_o_meter.py --csv off --ui_type terminal --int_pin 18'