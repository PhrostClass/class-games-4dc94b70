cd /c/Users/fepsi/ClassroomGames/tools
for g in 5 2 1 3 4 6; do echo "===== GRADE $g"; python milton.py harvest $g 2>&1 | grep -v "SyntaxWarning\|^  links\|^  covers\|^  imgs"; done
echo HARVEST_DONE
