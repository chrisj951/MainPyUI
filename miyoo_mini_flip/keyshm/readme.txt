docker build -t pyui_miyoomini .

mkdir output
docker run --rm -v ${PWD}/output:/output pyui_miyoomini cp set_monitor /output/
docker run --rm -v ${PWD}/output:/output pyui_miyoomini cp send_event /output/
docker run --rm -v ${PWD}/output:/output pyui_miyoomini cp getevent /output/