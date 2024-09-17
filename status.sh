set -x
time=`date "+%y%m%d-%H%M%S"`

grpcurl -plaintext -d {\"get_status\":{}} 192.168.100.1:9200 SpaceX.API.Device.Device/Handle >> get_status-$time.txt
