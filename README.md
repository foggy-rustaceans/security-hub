# security-hub
a security door camera system. 

A camera attached to a door captures an image of a visitor who wants to open the door and a PIN pad is used to input a password and trigger an attempted entrance event. Facial recognition is performed on the image and if the visitor matches a face with permission to open the door at that particular time, the door is opened. Possible extensions to the door sensors include a microphone for voice command recognition (e.g. recognizing “lock” or “open”) and a thermographic camera for body temperature detection (to prevent sick people from entering the building). Another possible extension includes using carbon monoxide and fire detectors, as well as an LED screen, to display a warning for carbon monoxide and fire detection at the front door.  

We plan to use a hub architecture that utilizes proof-carrying actuation similar to that found in [Soumya Basu’s trustless IoT paper](http://www.soumyabasu.com/assets/pdf/basu-hotedge20.pdf) [1]. Soumya’s work shows a lot of promise for adding an extra layer of security to IoT systems while allowing for high throughput and horizontal scalability. We think this is especially applicable for secure resource allocation systems such as doors with different access levels.  Our solution makes use of a variety of cloud resources to solve the problem. We host our system on an Azure IoT Hub, and simulated devices stream images to Azure Blob storage. When a user enters a PIN, it sends a message to our IoT Hub which triggers a service to look through the most recent footage capture by the camera in the Blob and performs facial recognition to check if an authorized user appeared on camera. If so, it sends a message to a simulated edge device to unlock the door and provide access.

## Install
 run each line
 ```
  python -m pip install Pillow
  pip install --upgrade azure-cognitiveservices-vision-face
  # blob storage
  pip install azure-storage-blob
 ```

 ## Run
  train a person group
  NOTE: if group already exists, delete it before re-training
  
  ```Python
  trainModel()
  ```