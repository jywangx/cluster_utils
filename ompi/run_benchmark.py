import subprocess 
import sys
import nums_from_string as ns
import pandas as pd

if len(sys.argv) != 4 :
        sys.stderr.write("使用方法: python "+sys.argv[0]+" <host> <np> <ppn>\n")
        exit(1)

host_list = sys.argv[1]
np        = int(sys.argv[2])
ppn       = int(sys.argv[3])

# ret = subprocess.run(["mpirun", "-np", "4", "/work/home/acehmpnhgy/install/omb/libexec/osu-micro-benchmarks/mpi/collective/osu_bcast", "-f"], capture_output=True)
# ret = subprocess.run("which mpirun", shell=True, capture_output=True)
# print(ret)

mpirun_str = "mpirun --map-by ppr:" + str(ppn) + ":node "
mpirun_str = mpirun_str + "-np " + str(np) + " "
mpirun_str = mpirun_str + "-H " + host_list + " "

# mpirun_str = "mpirun -np " + str(np) + " "

mca_global  = "-mca pml ucx -mca btl ^openib -mca coll_hcoll_enable 0 "
mca_tuned   = "-mca coll_tuned_priority 80 -mca coll_tuned_use_dynamic_rules true -mca coll_tuned_bcast_algorithm 6 -mca coll_tuned_bcast_algorithm_segmentsize 0 -mca coll_tuned_allreduce_algorithm 4 -mca coll_tuned_allgather_algorithm 3 -mca coll_tuned_gather_algorithm 2 -mca coll_tuned_gather_algorithm_segmentsize 0 "
mca_nsa     = mca_tuned + "-mca coll_nsa_enable true -mca coll_nsa_priority 100 -mca coll_sm_priority 90 "
mca_intert  = mca_tuned + mca_nsa + "-mca coll_nsa_inter_nsa false "
mca_default = mca_nsa + "-mca coll_nsa_alg_mode default "
mca_eager   = mca_nsa + "-mca coll_nsa_alg_mode eager "
mca_rndz    = mca_nsa + "-mca coll_nsa_alg_mode rndz "

omb_dir    = "/work/home/acehmpnhgy/install/omb/libexec/osu-micro-benchmarks/mpi/collective/"
omb_name   = omb_dir + "osu_gather "
omb_suffix = "-f -m :8388608"
omb_suffix = "-f -m :2097152"
# omb_suffix = "-f "

omb_commands = []
omb_commands.append(mpirun_str + mca_global + mca_tuned + omb_name + omb_suffix)
omb_commands.append(mpirun_str + mca_global + mca_intert + omb_name + omb_suffix)
omb_commands.append(mpirun_str + mca_global + mca_nsa + omb_name + omb_suffix)
omb_commands.append(mpirun_str + mca_global + mca_default + omb_name + omb_suffix)
# omb_commands.append(mpirun_str + mca_global + mca_eager + omb_name + omb_suffix)
# omb_commands.append(mpirun_str + mca_global + mca_rndz + omb_name + omb_suffix)
verbose = [
    '==============Tuned==============', 
    '===========Inter Tuned===========', 
    '===============NSA===============', 
    '=============Default============='
    # '==============Eager==============', 
    # '============Rendezvous==========='
]
# omb_command = mpirun_str + mca_global + mca_intert + omb_name + omb_suffix
# omb_command = mpirun_str + omb_name + omb_suffix

# print(omb_commands)

# res_cols = ['tuned', 'inter tuned', 'nsa', 'eager', 'rendezvous']
res_cols = ['tuned', 'inter tuned', 'nsa', 'default']
result_mean    = pd.DataFrame()
result_min     = pd.DataFrame()
result_median  = pd.DataFrame()
for i, cmd in enumerate(omb_commands):
    print('\n' + verbose[i])
    print(cmd)
    omb_res = pd.DataFrame(columns=['msg_size', 'avg', 'min', 'maximum'])

    iter_end = 8
    for i in range(0, iter_end):
        ret = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        res_lines = ret.stdout.splitlines()
        for line in res_lines:
            # print(line)
            line_nums = ns.get_nums(line)
            if line.startswith("#") or len(line_nums) != 5: continue
            # print(line_nums)
            row = pd.Series(line_nums[0:4], index=omb_res.columns)
            # print(row)
            omb_res = pd.concat([omb_res, row.to_frame().T], ignore_index=True) 
        print(str(i+1) + "/" + str(iter_end) + " completed.")
    omb_res['msg_size'] = omb_res['msg_size'].astype('int')
    res = omb_res.groupby("msg_size")["maximum"].quantile([0.01, 0.90]).unstack(level=1)
    print(res.to_string())
    print((res.loc[omb_res.msg_size, 0.01] < omb_res.maximum.values) & (omb_res.maximum.values < res.loc[omb_res.msg_size, 0.90]))
    res = omb_res.loc[((res.loc[omb_res.msg_size, 0.01] < omb_res.maximum.values) & (omb_res.maximum.values < res.loc[omb_res.msg_size, 0.90])).values]
    print(res)
    omb_res_mean    = res.groupby('msg_size').mean()
    omb_res_min     = omb_res.groupby('msg_size').min()
    omb_res_median  = omb_res.groupby('msg_size').median()
    print(omb_res_mean)    
    if i == 0:
        result_mean   = pd.concat([result_mean  , omb_res_mean['msg_size']]  , ignore_index=True, axis=1) 
        result_min    = pd.concat([result_min   , omb_res_min['msg_size']]   , ignore_index=True, axis=1) 
        result_median = pd.concat([result_median, omb_res_median['msg_size']], ignore_index=True, axis=1) 
    result_mean   = pd.concat([result_mean  , omb_res_mean['maximum']]  , ignore_index=True, axis=1) 
    result_min    = pd.concat([result_min   , omb_res_min['maximum']]   , ignore_index=True, axis=1) 
    result_median = pd.concat([result_median, omb_res_median['maximum']], ignore_index=True, axis=1) 
    if i == 2:
        print("平均值")
        print(result_mean)

result_mean.columns   = res_cols
result_min.columns    = res_cols
result_median.columns = res_cols
print("平均值")
print(result_mean)
# print("最小值")
# print(result_min)
# print("中位数")
# print(result_median)