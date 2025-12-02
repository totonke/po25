import serial
import datetime
# from datetime import datetime


print('-------Start-------')
ser = serial.Serial('/dev/ttyS0',9600)
try:
    while True:
        data= ser.readline()
        data_disp=data.strip().decode('UTF-8',errors='ignore')
        print(data_disp)
        
        l=data_disp.split(',')
        print(l)        
        
        dt_now = datetime.datetime.today().replace(microsecond=0)
        
        with open( 'LoRa_test.txt','a') as f:
            f.write(f'{dt_now},{data_disp}\n')
            
            
        
except KeyboardInterrupt:
    print('stop!')
    pass
ser.close()
        
