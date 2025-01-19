@echo off
setlocal

:: Check if a parameter was provided
if "%1"=="" (
    echo Usage: make_release.bat X.Y.Z
    exit /b 1
)

:: Assign the version from the first parameter
set VERSION=%1

:: Example git push command using the provided version
git push origin release-v%VERSION%

echo Successfully pushed release-v%VERSION%

mkdir tmp
cd tmp
git clone https://github.com/alessiomontone/Sous-Vide-Cooking-for-Engineers.git .
git remote add internal https://github.com/alessiomontone/Sous-Vide-Cooking-for-Engineers_internal.git
git fetch internal
git fetch internal --tags

git checkout -b release-v%VERSION%

git checkout internal/main -- . 
:: alternatively | git checkout internal/dev -- .
rm make_release.bat
git add .
git commit -m "Release version v%VERSION%"
git tag %VERSION%

git push origin release-v%VERSION%

git push origin --delete gh-pages
git subtree push --prefix "docs/build/html" origin gh-pages

echo Do a PULL REQUEST of the new branch v%VERSION% into main
