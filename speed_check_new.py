import cv2
import dlib
import time
import threading
import math
import cv2
import csv

# carCascade = cv2.CascadeClassifier('C:/Users/Mukeshjain/Desktop/speed_detection/vehicle-speed-check/myhaar.xml')
# video = cv2.VideoCapture('C:/Users/Mukeshjain/Desktop/speed_detection/vehicle-speed-check/i1.mp4')
cars_output={}
cars_output_time={}
def upload_video(path):
    carCascade = cv2.CascadeClassifier('./myhaar.xml')
    video = cv2.VideoCapture(path)
    return carCascade,video   

def estimateSpeed(location1, location2):
    d_pixels = math.sqrt(math.pow(location2[0] - location1[0], 2) + math.pow(location2[1] - location1[1], 2))
    # ppm = location2[2] / carWidht
    ppm = 16.8
    d_meters = d_pixels / ppm
    #print("d_pixels=" + str(d_pixels), "d_meters=" + str(d_meters))
    fps = 20
    speed = d_meters * fps * 3.6
    return speed


def trackMultipleObjects(carCascade,video):
    try:
        WIDTH = 1280
        HEIGHT = 720
        rectangleColor = (0, 255, 0)
        frameCounter = 0
        currentCarID = 0
        fps = 0
        
        carTracker = {}
        carNumbers = {}
        carLocation1 = {}
        carLocation2 = {}
        speed = [None] * 1000
        count=0
        
        # Write output to video file
        #out = cv2.VideoWriter('outpy.avi',cv2.VideoWriter_fourcc('M','J','P','G'), 10, (WIDTH,HEIGHT))

        fpsx = video.get(cv2.CAP_PROP_FPS)
        while True:
            rc, frame = video.read()
            start_time = time.time()

            
            image = cv2.resize(frame, (WIDTH, HEIGHT))
            resultImage = image.copy()
            
            frameCounter = frameCounter + 1
            
            carIDtoDelete = []

            for carID in carTracker.keys():
                trackingQuality = carTracker[carID].update(image)
                
                if trackingQuality < 7:
                    carIDtoDelete.append(carID)
                    
            for carID in carIDtoDelete:
                #print ('Removing carID ' + str(carID) + ' from list of trackers.')
                #print ('Removing carID ' + str(carID) + ' previous location.')
                #print ('Removing carID ' + str(carID) + ' current location.')
                carTracker.pop(carID, None)
                carLocation1.pop(carID, None)
                carLocation2.pop(carID, None)
            
            if not (frameCounter % 10):
                gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
                cars = carCascade.detectMultiScale(gray, 1.1, 13, 18, (24, 24))
                
                for (_x, _y, _w, _h) in cars:
                    x = int(_x)
                    y = int(_y)
                    w = int(_w)
                    h = int(_h)
                
                    x_bar = x + 0.5 * w
                    y_bar = y + 0.5 * h
                    
                    matchCarID = None
                
                    for carID in carTracker.keys():
                        trackedPosition = carTracker[carID].get_position()
                        
                        t_x = int(trackedPosition.left())
                        t_y = int(trackedPosition.top())
                        t_w = int(trackedPosition.width())
                        t_h = int(trackedPosition.height())
                        
                        t_x_bar = t_x + 0.5 * t_w
                        t_y_bar = t_y + 0.5 * t_h
                    
                        if ((t_x <= x_bar <= (t_x + t_w)) and (t_y <= y_bar <= (t_y + t_h)) and (x <= t_x_bar <= (x + w)) and (y <= t_y_bar <= (y + h))):
                            matchCarID = carID
                    
                    if matchCarID is None:
                        tracker = dlib.correlation_tracker()
                        tracker.start_track(image, dlib.rectangle(x, y, x + w, y + h))
                        
                        carTracker[currentCarID] = tracker
                        carLocation1[currentCarID] = [x, y, w, h]

                        currentCarID = currentCarID + 1
            
            cv2.line(resultImage,(0,245),(1280,245),(0,0,0),1)
            cv2.line(resultImage,(0,285),(1280,285),(0,0,0),1)


            for carID in carTracker.keys():
                trackedPosition = carTracker[carID].get_position()
                        
                t_x = int(trackedPosition.left())
                t_y = int(trackedPosition.top())
                t_w = int(trackedPosition.width())
                t_h = int(trackedPosition.height())
                
                cv2.rectangle(resultImage, (t_x, t_y), (t_x + t_w, t_y + t_h), rectangleColor, 4)
                
                # speed estimation
                carLocation2[carID] = [t_x, t_y, t_w, t_h]
            
            end_time = time.time()
            
            if not (end_time == start_time):
                fps = 1.0/(end_time - start_time)
            
            #cv2.putText(resultImage, 'FPS: ' + str(int(fps)), (620, 30),cv2.FONT_HERSHEY_SIMPLEX, 0.75, (0, 0, 255), 2)


            for i in carLocation1.keys():    
                if frameCounter % 1 == 0:
                    [x1, y1, w1, h1] = carLocation1[i]
                    [x2, y2, w2, h2] = carLocation2[i]
            
                    # print 'previous location: ' + str(carLocation1[i]) + ', current location: ' + str(carLocation2[i])
                    carLocation1[i] = [x2, y2, w2, h2]
            
                    # print 'new previous location: ' + str(carLocation1[i])
                    if [x1, y1, w1, h1] != [x2, y2, w2, h2]:
                        if (speed[i] == None or speed[i] == 0) and y1 >= 245 and y1 <= 285:
                            speed[i] = estimateSpeed([x1, y1, w1, h1], [x2, y2, w2, h2])
                            

                        #if y1 > 275 and y1 < 285:
                        if speed[i] != None and y1 >= 245 :
                            cv2.putText(resultImage, str(int(speed[i])) + " km/hr", (int(x1 + w1/2), int(y1-5)),cv2.FONT_HERSHEY_SIMPLEX, 0.75, (255, 0, 0), 2)
                            car=resultImage[y1:y1+h1+70,x1:x1+w1+70]
                            #cv2.imwrite("output/%dcar%d.jpg" %speed[i],car)
                            cv2.imwrite("./static/detections/speed/car-%s-%d.jpg" %
                                        (str(i), speed[i]), car)
                            cars_output[i]=int(speed[i])
                            cars_output_time[i]=count/fpsx
                            print ('CarID ' + str(i) + ': speed is ' + str("%.2f" % round(speed[i], 0)) + ' km/h.\n')

                        #else:
                        #    cv2.putText(resultImage, "Far Object", (int(x1 + w1/2), int(y1)),cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)

                            #print ('CarID ' + str(i) + ' Location1: ' + str(carLocation1[i]) + ' Location2: ' + str(carLocation2[i]) + ' speed is ' + str("%.2f" % round(speed[i], 0)) + ' km/h.\n')
            imS = cv2.resize(resultImage, (640, 480))
            # cv2.imshow("output", imS)
            cv2.imshow('Result', imS)
            # Write the frame into the file 'output.avi'
            #out.write(resultImage)

            if cv2.waitKey(33) == 27:
                break
            count+=1
        
        cv2.destroyAllWindows()
    except Exception:
        #print(cars_output)
        #print(cars_output_time)
        csvfile = open('./static/detections/speed/speed.csv', 'a', newline='')
        obj = csv.writer(csvfile)
        obj.writerow(("Car Id.","Speed","Timestamp"))
        for (k1,v1),(k2,v2) in zip(cars_output.items(),cars_output_time.items()):
            obj.writerow([k1,v1,v2])
        csvfile.close()
        print("Over")

def speed_detection(path):
    carCascade,video=upload_video(path)
    trackMultipleObjects(carCascade,video)

# speed_detection("./i1.mp4")
