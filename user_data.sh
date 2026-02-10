cat > user_data.sh << 'EOF'
#!/bin/bash
apt-get update
apt-get install -y docker.io docker-compose git
systemctl start docker
systemctl enable docker
# Additional setup logic here
EOF