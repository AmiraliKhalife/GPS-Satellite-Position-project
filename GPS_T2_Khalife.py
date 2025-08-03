import re
import numpy as np
import csv
import matplotlib.pyplot as plt
from math import sin, cos, sqrt, atan2
from mpl_toolkits.mplot3d import Axes3D

MU = 3.986005e14
omega_e = 7.2921151467e-5


def plot_all_paths(data):

    fig = plt.figure()
    ax = fig.add_subplot(111, projection='3d')
    ax.set_title('3D Path of All Satellites')
    ax.set_xlabel('X (m)')
    ax.set_ylabel('Y (m)')
    ax.set_zlabel('Z (m)')

    for prn in sorted(data.keys()):
        try:
            t_start, t_end = get_time_range(data[prn])
            times = generate_times(t_start, t_end)
            positions = Compute_satellite_position(data[prn], times)
            xs, ys, zs = zip(*[(x, y, z) for _, x, y, z in positions])
            ax.plot(xs, ys, zs, label=prn)
        except Exception as e:
            print(f" Error processing {prn}: {e}")


    plt.tight_layout()
    plt.show()

def Read_rinex(filepath):

    with open(filepath, 'r') as f:
        lines = f.readlines()

    idx = 0
    while 'END OF HEADER' not in lines[idx]:
        idx += 1
    idx += 1

    nav = {}
    field_names = [
        'a0','a1','a2','IOD','Crs','deltan','M0',
        'Cuc','e','Cus','sqrt_a','toe','Cic','Omega','Cis',
        'i0','Crc','omega','Omegadot','idot','L2','GPS_week',
        'L2_P','sat_acc','sat_health','TGD','IODC','trans_time','spare'
    ]

    while idx + 7 < len(lines):
        block = lines[idx:idx+8]
        idx += 8

        prn = block[0][:3].strip()
        if not prn:
            continue
        nav.setdefault(prn, [])

        yr = int(block[0][3:8].strip())
        mon = int(block[0][8:11].strip())
        dy = int(block[0][11:14].strip())
        hr = int(block[0][14:17].strip())
        mn = int(block[0][17:20].strip())
        sc = float(block[0][20:23].strip())

        vals = []
        for ln in block:
            parts = re.findall(r'[+-]?\d+\.\d+D[+-]?\d+', ln)
            vals.extend([float(p.replace('D','E')) for p in parts])

        if len(vals) < len(field_names):
            continue

        data = dict(zip(field_names, vals[:len(field_names)]))
        data.update({'year':yr,'month':mon,'day':dy,'hour':hr,'minute':mn,'second':sc})
        nav[prn].append(data)

    return nav

def gps_seconds_from_datetime(year, month, day, hour, minute, second):

    a = (14 - month) // 12
    y = year + 4800 - a
    m = month + 12 * a - 3
    jd = day + ((153 * m + 2) // 5) + 365*y + y//4 - y//100 + y//400 - 32045
    jd = jd + (hour - 12)/24 + minute/1440 + second/86400
    jd_gps = 2444244.5
    gps_secs_total = (jd - jd_gps)*86400
    return gps_secs_total % (7*86400)

def epoch_to_gps_seconds(r):

    return gps_seconds_from_datetime(r['year'], r['month'], r['day'], r['hour'], r['minute'], r['second'])

def get_time_range(prn_data):

    times = [epoch_to_gps_seconds(r) for r in prn_data]
    return min(times), max(times)

def generate_times(start, end, step=30):

    return np.arange(start, end + 1e-9, step)

def solve_eccentric_anomaly(M, e, tol=1e-12, max_iter=10):

    E = M
    for _ in range(max_iter):
        f = E - e * sin(E) - M
        f_prime = 1 - e * cos(E)
        dE = -f / f_prime
        E += dE
        if abs(dE) < tol:
            break
    return E

def Compute_satellite_position(prn_data, t_emission):
    positions = []
    for t in t_emission:
        eph = min(prn_data, key=lambda r: abs(t - epoch_to_gps_seconds(r)))

        sqrt_a = eph['sqrt_a']
        a = sqrt_a**2
        e = eph['e']
        M0 = eph['M0']
        omega = eph['omega']
        I0 = eph['i0']
        Omega0 = eph['Omega']
        deltan = eph['deltan']
        toe = eph['toe']
        IDOT = eph['idot']
        Cuc = eph['Cuc']; Cus = eph['Cus']
        Crc = eph['Crc']; Crs = eph['Crs']
        Cic = eph['Cic']; Cis = eph['Cis']

        tk = t - toe
        if tk > 302400:
            tk -= 604800
        elif tk < -302400:
            tk += 604800

        n0 = sqrt(MU / a**3)
        n = n0 + deltan
        Mk = M0 + n * tk
        Ek = solve_eccentric_anomaly(Mk, e)
        vk = atan2(sqrt(1 - e**2) * sin(Ek), cos(Ek) - e)
        phi = vk + omega
        uk = phi + Cus * sin(2*phi) + Cuc * cos(2*phi)
        rk = a * (1 - e * cos(Ek)) + Crs * sin(2*phi) + Crc * cos(2*phi)
        Ik = I0 + IDOT * tk + Cis * sin(2*phi) + Cic * cos(2*phi)
        Omega_k = Omega0 + (eph['Omegadot'] - omega_e) * tk - omega_e * toe

        x_prime = rk * cos(uk)
        y_prime = rk * sin(uk)

        X = x_prime * cos(Omega_k) - y_prime * cos(Ik) * sin(Omega_k)
        Y = x_prime * sin(Omega_k) + y_prime * cos(Ik) * cos(Omega_k)
        Z = y_prime * sin(Ik)

        positions.append((t, X, Y, Z))
    return positions

def save_to_csv(data, path):
    with open(path, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['t_gps', 'x', 'y', 'z'])
        for t, x, y, z in data:
            writer.writerow([f"{t:.11f}", x, y, z])

def plot_3d_path(data, label=''):
    xs, ys, zs = zip(*[(x, y, z) for _, x, y, z in data])
    fig = plt.figure()
    ax = fig.add_subplot(111, projection='3d')
    ax.plot(xs, ys, zs, label=label)
    ax.set_xlabel('X (m)')
    ax.set_ylabel('Y (m)')
    ax.set_zlabel('Z (m)')
    ax.set_title('3D path of satellite')
    if label:
        ax.legend()
    plt.tight_layout()
    plt.show()

def process_prn(filepath, prn, save_csv=True, show_plot=True):

    data = Read_rinex(filepath)

    if prn not in data:
        print(f" PRN {prn} not found in file.")
        return None

    print(f"\n Processing PRN: {prn}")

    t_start, t_end = get_time_range(data[prn])
    print(f"  Start (GPS sec): {t_start:.11f}")
    print(f"  End   (GPS sec): {t_end:.11f}")

    times = generate_times(t_start, t_end)
    print(f"  Number of epochs (30s step): {len(times)}")

    positions = Compute_satellite_position(data[prn], times)

    if save_csv:
        csv_name = f"{prn}_positions.csv"
        save_to_csv(positions, csv_name)
        print(f" CSV file saved: {csv_name}")

    if show_plot:
        plot_3d_path(positions, label=prn)

    return positions

if __name__ == "__main__":
    filepath = "GODS00USA_R_20240010000_01D_GN.rnx"
    prn = input("Enter the PRN (for example: G05): ").strip().upper()
    process_prn(filepath, prn)

    show_all = input("Show all satellite paths? (y/n): ").strip().lower()
    if show_all == 'y':
        data = Read_rinex(filepath)
        plot_all_paths(data)
