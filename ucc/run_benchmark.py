import subprocess 
import sys
import nums_from_string as ns
import pandas as pd

if len(sys.argv) < 2 :
        sys.stderr.write("Usage: python "+sys.argv[0]+" <host>\n")
        exit(1)

host_list = sys.argv[1]

nnodes = [4, 8, 16, 32]
ppns   = [4, 8, 16, 32]

start_count = int(1)
end_count   = int(16*1024*1024)

cl_hier_env = "-x UCC_CL_HIER_TLS=ucp,sharp,self -x UCC_CL_BASIC_TLS=ucp,sharp -x UCC_CLS=hier "
cl_hier_env = cl_hier_env + "-x UCC_CL_HIER_NODE_LEADERS_SBGP_TLS=ucp,sharp "
cl_hier_env = cl_hier_env + "-x UCC_CL_HIER_TUNE=allreduce:0-inf:@rab "

cl_basic_env = "-x UCC_CL_BASIC_TLS=ucp,sharp -x UCC_CLS=basic "

# sharp_hier_env = [
#     "-x UCC_TL_SHARP_TUNE=0 ",
#     "-x UCC_TL_SHARP_DEVICES=mlx5_2:1 -x UCC_TL_SHARP_TUNE=allreduce:0-inf -x SHARP_COLL_ENABLE_SAT=0 ",
#     "-x UCC_TL_SHARP_DEVICES=mlx5_2:1 -x UCC_TL_SHARP_TUNE=allreduce:0-inf -x SHARP_COLL_ENABLE_SAT=1 "
# ]

basic_inter_env = [
    "-x UCC_TL_SHARP_TUNE=0 ",
    "-x UCC_TL_SHARP_DEVICES=mlx5_2:1 -x UCC_TL_SHARP_TUNE=reduce_scatter:0-inf -x SHARP_COLL_ENABLE_SAT=0 -x UCC_TL_SHARP_RS_SWITCH_THERSH=" + str(end_count*8) + " ",
    "-x UCC_TL_SHARP_DEVICES=mlx5_2:1 -x UCC_TL_SHARP_TUNE=reduce_scatter:0-inf -x SHARP_COLL_ENABLE_SAT=1 -x SHARP_COLL_SAT_THRESHOLD=1 -x UCC_TL_SHARP_RS_SWITCH_THERSH=256 ",
    "-x UCC_TL_SHARP_DEVICES=mlx5_2:1 -x UCC_TL_SHARP_TUNE=reduce_scatter:0-inf -x SHARP_COLL_ENABLE_SAT=1 -x UCC_TL_SHARP_RS_SWITCH_THERSH=" + str(end_count*8) + " "
]

sharp_tag = [
    "no-sharp",
    "llt-arw",
    "sat-nr",
    "sat-arw"
]

ucc_perftest = "ucc_perftest -c reduce_scatter -b " + str(start_count) + " -e " + str(end_count)

ucc_perf_cmds = []
ucc_perf_tags = []

# CL/BASIC PPN=1
ppn = 1
for nnode in nnodes:
    mpirun_str = "mpirun --map-by ppr:" + str(ppn) + ":node "
    mpirun_str = mpirun_str + "-np " + str(nnode*ppn) + " "
    mpirun_str = mpirun_str + "-H " + host_list + " --report-bindings "
    for i, basic_inter in enumerate(basic_inter_env):
        tags = {
            "nnode": nnode,
            "ppn"  : ppn,
            "cl"   : "basic",
            "sharp": sharp_tag[i]
        }
        ucc_perf_tags.append(tags)
        ucc_perf_cmds.append(mpirun_str + cl_basic_env + basic_inter + ucc_perftest)

# # CL/BASIC TL/UCP PPN>1
# ppn = 1
# for nnode in nnodes:
#     for ppn in ppns:
#         mpirun_str = "mpirun --map-by ppr:" + str(ppn) + ":node "
#         mpirun_str = mpirun_str + "-np " + str(nnode*ppn) + " "
#         mpirun_str = mpirun_str + "-H " + host_list + " --report-bindings "
#         tags = {
#             "nnode": nnode,
#             "ppn"  : ppn,
#             "cl"   : "basic",
#             "sharp": sharp_tag[0]
#         }
#         ucc_perf_tags.append(tags)
#         ucc_perf_cmds.append(mpirun_str + cl_basic_env + basic_inter_env[0] + ucc_perftest)

# # CL/HIER
# for nnode in nnodes:
#     for ppn in ppns:
#         mpirun_str = "mpirun --map-by ppr:" + str(ppn) + ":node "
#         mpirun_str = mpirun_str + "-np " + str(nnode*ppn) + " "
#         mpirun_str = mpirun_str + "-H " + host_list + " --report-bindings "
#         for i, sharp_hier in enumerate(sharp_hier_env):
#             tags = {
#                 "nnode": nnode,
#                 "ppn"  : ppn,
#                 "cl"   : "hire",
#                 "sharp": sharp_tag[i]
#             }
#             ucc_perf_tags.append(tags)
#             ucc_perf_cmds.append(mpirun_str + cl_hier_env + sharp_hier + ucc_perftest)

# for i, cmd in enumerate(ucc_perf_cmds):
#     print(ucc_perf_tags[i])
#     print(cmd)
#     print("")
# print(ucc_perf_cmds)

upt_res = pd.DataFrame(columns=['count', 'msg_size', 'avg', 'min', 'maximum', 'nnode', 'ppn', 'cl', 'sharp'])
for i, cmd in enumerate(ucc_perf_cmds):
    print(ucc_perf_tags[i])
    print(cmd)
    print("Testing...")
    print("")

    ret = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    res_lines = ret.stdout.splitlines()
    ok = False
    for line in res_lines:
        # print(line)
        line_nums = ns.get_nums(line)
        if line.startswith("[") or len(line_nums) != 5: continue
        # print(line_nums)
        series_data = line_nums[0:5] + list(ucc_perf_tags[i].values())
        print(series_data)
        row = pd.Series(series_data, index=upt_res.columns)
        upt_res = pd.concat([upt_res, row.to_frame().T], ignore_index=True) 
        ok = True
    if not ok:
        print("Test fail.")
        print("")

print(upt_res)    

upt_res.to_csv('output.csv', index=False)