

gcloud compute scp --recurse ./fdtd_PCB_extensions instance-2:~/
gcloud compute scp --recurse ./run instance-2:~/



gcloud compute ssh instance-2
curl curl https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh > conda.sh
pip install torch fdtd pyevtk cairosvg

cd fdtd_PCB_extensions
python setup.py develop

gcloud compute scp --recurse ./fdtd_PCB_extensions/ gpu-instance:~/
gcloud compute scp --recurse ./run gpu-instance:~/

gcloud compute disks create gpu-disk --type pd-ssd --image-family pytorch-latest-gpu --image-project deeplearning-platform-release --size=50
# us-central1-f
