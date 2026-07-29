import glob

old_nq = """                        if nq_first_dir == 1:
                            ext = nq_h_arr[i] - ib_nq_h
                            if ext > nq_max_ext: nq_max_ext = ext
                            if nq_l_arr[i] < ib_nq_l:
                                nq_is_double = 2
                                break
                        else:
                            ext = ib_nq_l - nq_l_arr[i]
                            if ext > nq_max_ext: nq_max_ext = ext
                            if nq_h_arr[i] > ib_nq_h:
                                nq_is_double = 2
                                break"""

new_nq = """                        if nq_first_dir == 1:
                            if nq_l_arr[i] < ib_nq_l:
                                nq_is_double = 2
                                break
                            ext = nq_h_arr[i] - ib_nq_h
                            if ext > nq_max_ext: nq_max_ext = ext
                        else:
                            if nq_h_arr[i] > ib_nq_h:
                                nq_is_double = 2
                                break
                            ext = ib_nq_l - nq_l_arr[i]
                            if ext > nq_max_ext: nq_max_ext = ext"""

old_es = """                        if es_first_dir == 1:
                            ext = es_h_arr[i] - ib_es_h
                            if ext > es_max_ext: es_max_ext = ext
                            if es_l_arr[i] < ib_es_l:
                                es_is_double = 2
                                break
                        else:
                            ext = ib_es_l - es_l_arr[i]
                            if ext > es_max_ext: es_max_ext = ext
                            if es_h_arr[i] > ib_es_h:
                                es_is_double = 2
                                break"""

new_es = """                        if es_first_dir == 1:
                            if es_l_arr[i] < ib_es_l:
                                es_is_double = 2
                                break
                            ext = es_h_arr[i] - ib_es_h
                            if ext > es_max_ext: es_max_ext = ext
                        else:
                            if es_h_arr[i] > ib_es_h:
                                es_is_double = 2
                                break
                            ext = ib_es_l - es_l_arr[i]
                            if ext > es_max_ext: es_max_ext = ext"""

old_filter = "        df['MinsFromStart'] = df['DateTime'].apply(calc_mins_from_start)"
new_filter = "        df['MinsFromStart'] = df['DateTime'].apply(calc_mins_from_start)\n        df = df[df['MinsFromStart'] <= 1380]"

files = glob.glob(r"d:\Antigravity\Workspace\python\ib_extension_test*.py")
for f in files:
    with open(f, 'r', encoding='utf-8') as file:
        content = file.read()
    
    if "df = df[df['MinsFromStart'] <= 1380]" not in content:
        content = content.replace(old_filter, new_filter)
        content = content.replace(old_nq, new_nq)
        content = content.replace(old_es, new_es)
        
        with open(f, 'w', encoding='utf-8') as file:
            file.write(content)
        print(f"Patched {f}")
    else:
        print(f"Already patched {f}")
