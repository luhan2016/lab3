#!/bin/bash
for i in `seq 1 8`; do
	curl -d 'entry=vessel1:'${i} -X 'POST' 'http://10.1.0.1/board' &
	curl -d 'entry=vessel2:'${i} -X 'POST' 'http://10.1.0.2/board' &
	curl -d 'entry=vessel3:'${i} -X 'POST' 'http://10.1.0.3/board' 
done
