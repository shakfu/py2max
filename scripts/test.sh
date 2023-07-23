
# $1: python script to generate a maxpat
# $2: a conventially made maxpat to compare $1 with


PYSCRIPT=$1
TO_COMPARE_WITH=$2
NAME=`basename -s .py `
MAXPAT=${NAME}.maxpat

mkdir -p outputs
python3 $1 && \
	./scripts/convert.py outputs/${MAXPAT} && \
	./scripts/compare.py -y outputs/${MAXPAT} ${TO_COMPARE_WITH}
echo "done"