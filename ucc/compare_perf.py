import pandas as pd
import sys

if len(sys.argv) < 4 :
    sys.stderr.write("Usage: python "+sys.argv[0]+" <nnode> <ppn> <filename>\n")
    exit(1)

input_nnode = int(sys.argv[1])
input_ppn   = int(sys.argv[2])

csv_filename = sys.argv[3]

# Read CSV file
df = pd.read_csv(csv_filename)

# Filter data by ppn and nnode
filtered_df = df[(df['ppn'] == input_ppn) & (df['nnode'] == input_nnode)]

# Get all different msg_size
msg_sizes = filtered_df['msg_size'].unique()

# For all msg_size
msg_df = filtered_df[filtered_df['msg_size'] == msg_sizes[0]]
header = "msg_size"
for cl, sharp in msg_df.groupby(['cl', 'sharp']):
    header = header + f",{cl[0]}:{cl[1]}"
print(header)
for msg_size in msg_sizes:
    msg_df = filtered_df[filtered_df['msg_size'] == msg_size]
    
    # Print vlaue of 'avg' of different <cl, sharp>
    line = f"{msg_size}"
    for cl, sharp in msg_df.groupby(['cl', 'sharp']):
        avg_value = sharp['avg'].mean()
        line = line + f",{avg_value:.2f}"
    print(line)
