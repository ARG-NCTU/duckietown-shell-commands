eval "$(ssh-agent -s)"
ssh-add -k ~/.ssh/*
ssh -T git@github.com
