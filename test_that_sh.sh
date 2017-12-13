TEST_BITS=0
TEST_SAMPLE_NUM=2

#argument to randomize the selected rewritter procedures or not.
if [ "$1" = 0 ]
then
  TEST_SAMPLE_NUM=2
  for i in `seq $TEST_SAMPLE_NUM`
  do
    temp="`expr $((RANDOM % 2))`,`expr $((RANDOM % 2))`,`expr $((RANDOM % 2))`,`expr $((RANDOM % 2))`,`expr $((RANDOM % 2))`,`expr $((RANDOM % 2))`,`expr $((RANDOM % 2))`,`expr $((RANDOM % 2))`"
    echo $temp
    TEST_BITS[$i]=$temp
  done

fi

#don't randomize.
if [ "$1" = 1 ]
then
  TEST_SAMPLE_NUM=1
  TEST_BITS[1]="1,1,1,1,1,1,1,1"
fi



for dir_name in p01 #p02 p03
do
  for i in `seq $TEST_SAMPLE_NUM`
  do
    for j in `seq $2`
    do
      test_str=${TEST_BITS[$i]}
      echo $test_str
      if [ "$j" = 1 ]
      then
        python3 test_that_sh.py $dir_name/fxn.s asm/fxn$j.s  $test_str;  #rewrite the code
      else
        python3 test_that_sh.py asm/fxn$(($j-1)).s asm/fxn$j.s $test_str;  #rewrite the code
      fi
      as asm/fxn$j.s -o fxn.o;  #assemble the rewritten stuff
      mv fxn.o  $dir_name;
      cd $dir_name;
      g++ -std=c++11 -O3 main.cc fxn.o;  #compile with rewritten function
      #run stoke and optimize
      make extract;
      make testcase;
      make search_synth;
      #verify results
      if [ "$1" = 0 ]
      then
        stoke debug verify --config verify.conf > res/$test_str.vero;
      fi

      if [ "$1" = 1 ]
      then
        stoke debug verify --config verify.conf > res/$test_str.iter$j;
      fi

      cd ..
    done
  done

done


if [ "$1" = 0 ]
then
  python gen_csv.py 0 #publish results
fi

if [ "$1" = 1 ]
then
  python gen_csv.py 1
fi
