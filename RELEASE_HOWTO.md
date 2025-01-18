# Release

from a support forlder "CFE_PUBLIC"

git clone https://github.com/alessiomontone/Sous-Vide-Cooking-for-Engineers_internal.git .

rm -rf .git
rm RELEASE_HOWTO.md

git init --initial-branch=main
git remote add origin https://github.com/alessiomontone/Sous-Vide-Cooking-for-Engineers.git
git add .
git commit -m "Release 0.1.2"
git tag v0.1.2
git push origin main