import { useState, useRef , useEffect} from 'react';
import Webcam from 'react-webcam';
import Dropzone from 'react-dropzone';


const FormSection = ({ generateResponse, handleImage }) => {
    const [newQuestion, setNewQuestion] = useState('');
    const webcamRef = useRef(null);
    const [isCameraOpen, setIsCameraOpen] = useState(false);
    const [selectedImage, setSelectedImage] = useState(null);
  
    const handleCapturePhoto = () => {
        const canvas = webcamRef.current.getCanvas();
        const dataUrl = canvas.toDataURL('image/jpeg');      
        setSelectedImage(dataUrl);
        setIsCameraOpen(false);            
    };

    useEffect(() => {
        // Access the media devices and select the back camera
        navigator.mediaDevices.enumerateDevices()
          .then(devices => {
            const videoDevices = devices.filter(device => device.kind === 'videoinput');
            const backCamera = videoDevices.find(device => device.label.toLowerCase().includes('back'));
            
            if (backCamera) {
              const constraints = { deviceId: { exact: backCamera.deviceId } };
              webcamRef.current.video.srcObject.getVideoTracks().forEach(track => track.stop());
              webcamRef.current.video.srcObject = null;
              navigator.mediaDevices.getUserMedia({ video: constraints })
                .then(stream => {
                  webcamRef.current.video.srcObject = stream;
                })
                .catch(error => {
                  console.error('Error accessing back camera:', error);
                });
            }
          })
          .catch(error => {
            console.error('Error enumerating media devices:', error);
          });
      }, []);

    useEffect(() => {
        if (selectedImage) {
          // Perform actions that depend on the selectedImage
          handleImage(selectedImage);
        }
      }, [selectedImage]);

    const handleToggleCamera = () => {
        setIsCameraOpen(prevState => !prevState);
    };
  
    const handleUploadImage = (acceptedFiles) => {
      // Assuming you want to upload the first selected file
      const uploadedFile = acceptedFiles[0];
      const reader = new FileReader();
      reader.onload = () => {
        const dataUrl = reader.result;
        setSelectedImage(dataUrl);        
      };
      reader.readAsDataURL(uploadedFile);      
            
    };

    
    return (
        <div className="form-section">
            <textarea
                rows="5"
                className="form-control"
                placeholder="Ask me anything..."
                value={newQuestion}
                onChange={(e) => setNewQuestion(e.target.value)}
            ></textarea>

        

            <button className="btn" onClick={() => generateResponse(newQuestion, setNewQuestion)}>
                Find
            </button>


            {isCameraOpen ? (
                <>
                <Webcam ref={webcamRef} screenshotFormat="image/jpeg" videoConstraints={{ facingMode: 'environment' }} />
                    <button className="btn" type="button" onClick={handleCapturePhoto}>
                        Capture Photo
                    </button>
                </>
            ): (
                <button className="btn" type="button" onClick={handleToggleCamera}>
                Open Camera
                </button>
            )}
            {/* Render the file upload component */}
            <Dropzone onDrop={handleUploadImage}>
                {({ getRootProps, getInputProps }) => (
                <div {...getRootProps()}>
                    <button className="btn"><input {...getInputProps()} />
                    Upload a image file
                    </button>
                </div>
                )}
            </Dropzone>
            
        </div>
    )
}

export default FormSection