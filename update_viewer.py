import os
import json

SCENE_DIR = 'results'
OUTPUT_DIR = 'scenes'
ROOT_INDEX = 'index.html'

TYPES = ['SwinIR', 'PFT-SR_TSD-SR']

# Map suffixes to display titles for each type
SUFFIX_MAPPING = {
    'SwinIR': {
        '_LR.png': 'LR',
        '_HR.png': 'HR',
        '_SwinIR_C.png': 'SwinIR-C',
        '_SwinIR_RW.png': 'SwinIR-RW',
        '_SwinIR_1.png': 'Our1(edge)',
        '_SwinIR_2.png': 'Our2(final)'
    },
    'PFT-SR_TSD-SR': {
        '_LR.png': 'LR',
        '_HR.png': 'HR',
        '_PFT.png': 'PFT-SR',
        '_TSD-SR.png': 'TSD-SR',
        '_TSD_SR_PFT_1.png': 'Our1(edge)',
        '_TSD_SR_PFT_2.png': 'Our2(final)',
        '_PFT_TSD_GFPGAN.png': 'Our2+GFPGAN'
    }
}

PRIORITY = {
    'SwinIR': ['LR', 'HR', 'SwinIR-C', 'SwinIR-RW', 'Our1(edge)', 'Our2(final)'],
    'PFT-SR_TSD-SR': ['LR', 'HR', 'PFT-SR', 'TSD-SR', 'Our1(edge)', 'Our2(final)', 'Our2+GFPGAN']
}

def extract_info():
    if not os.path.exists(SCENE_DIR):
        print(f"Directory {SCENE_DIR} not found.")
        return {}
    images = os.listdir(SCENE_DIR)
    
    base_prefixes = []
    for img in images:
        if img.endswith('_HR.png'):
            base_prefixes.append(img.replace('_HR.png', ''))
            
    datasets_dict = {}
    for bp in base_prefixes:
        parts = bp.split('_', 1)
        dataset_name = parts[0]
        if dataset_name not in datasets_dict:
            datasets_dict[dataset_name] = []
        datasets_dict[dataset_name].append(bp)
        
    return datasets_dict

def update_dataset_data(type_name, dataset_name, base_prefixes):
    dataset_path = os.path.join(OUTPUT_DIR, type_name, dataset_name)
    if not os.path.exists(dataset_path):
        os.makedirs(dataset_path)

    image_boxes = []
    base_prefixes = sorted(base_prefixes)
    
    for bp in base_prefixes:
        img_name = bp.split('_', 1)[1] if '_' in bp else bp
        elements = []
        
        for suffix, cat_title in SUFFIX_MAPPING[type_name].items():
            img_filename = f"{bp}{suffix}"
            scene_path = f"{SCENE_DIR}/{img_filename}"
            if os.path.exists(os.path.join(SCENE_DIR, img_filename)):
                el = {
                    "title": cat_title,
                    "version": "-",
                    "image": f"../../../{scene_path}"
                }
                if cat_title == 'LR':
                    el["scale"] = 4
                elements.append(el)
        
        priority_list = PRIORITY[type_name]
        elements.sort(key=lambda x: priority_list.index(x["title"]) if x["title"] in priority_list else 999)
        
        if elements:
            image_boxes.append({
                "title": img_name,
                "elements": elements
            })

    data_content = f"const data = \n{json.dumps({'imageBoxes': image_boxes}, indent=4)}\n"
    with open(os.path.join(dataset_path, 'data.js'), 'w', encoding='utf-8') as f:
        f.write(data_content)
        
    dataset_html = generate_dataset_html(dataset_name)
    with open(os.path.join(dataset_path, 'index.html'), 'w', encoding='utf-8') as f:
        f.write(dataset_html)
        
    if image_boxes and image_boxes[0]['elements']:
        first_img = image_boxes[0]['elements'][0]['image']
        if first_img.startswith("../../../"):
            return first_img.replace("../../../", "../../", 1)
        else:
            return f"{dataset_name}/{first_img}"
    return None

def generate_dataset_html(dataset_name):
    return f"""<!DOCTYPE doctype html>
<html lang="en">
<head>
    <meta charset="utf-8" />
    <meta content="width=device-width, initial-scale=1.0" name="viewport" />
    <meta content="Rendering Results" name="description" />
    <title>{dataset_name}</title>
    <link href="https://fonts.googleapis.com/css?family=Roboto:400,600" rel="stylesheet" type="text/css" />
    <link href="../../../utils/report.css" rel="stylesheet" />
    <script src="https://kit.fontawesome.com/b3ad2626f1.js"></script>
    <script src="./data.js"></script>
    <script src="../../../utils/react.js"></script>
    <script src="../../../utils/react-dom.js"></script>
    <script src="../../../utils/ImageBox.js"></script>
    <script src="../../../utils/Chart.js"></script>
    <script src="../../../utils/ChartBox.js"></script>
    <script src="../../../utils/TableBox.js"></script>
    <script src="../../../utils/CopyrightBox.js"></script>
    <script src="../../../utils/jeri.js"></script>
    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
    <script src="../../../utils/PlotBox.js"></script>
</head>
<script type="text/javascript">
    function setup() {{
        var local = true;
        content = document.getElementById("content");
        var box = document.getElementById('image-box');
        var help = document.createElement('div');
        var helpText = "Use mouse wheel to zoom in/out, click and drag to pan. Press keys [1], [2], ... to switch between individual images.";
        if (!local) {{
            helpText += " Press [?] to see more keybindings.";
        }}
        help.appendChild(document.createTextNode(helpText));
        help.className = "help";
        box.appendChild(help);
        if (local) {{
            new ImageBox(content, data['imageBoxes']);
        }} else {{
            var jeri = document.createElement('div');
            jeri.className = "jeri";
            var viewer = Jeri.renderViewer(jeri, data["jeri"]);
            box.appendChild(jeri);
            viewer.setState({{ activeRow: 1 }});
            content.appendChild(box);
        }}
        new TableBox(content, "Statistics", data["stats"]);
        new PlotBox(content, "Convergence Plots", data["stats"]);
    }}
</script>
<body onload="setup();">
    <div class="content scene-content" id="content">
        <div class="image-box" id="image-box">
            <p><a href="../index.html"><i class="fas fa-arrow-left"></i> Back to index</a></p>
            <h1 class="title">{dataset_name}</h1>
        </div>
    </div>
</body>
</html>
"""

def update_type_index(type_name, datasets_data):
    type_path = os.path.join(OUTPUT_DIR, type_name)
    if not os.path.exists(type_path):
        os.makedirs(type_path)
        
    html_lines = [
        '<!DOCTYPE doctype html>',
        '<html lang="en">',
        '<head>',
        '    <meta charset="utf-8" />',
        '    <meta content="width=device-width, initial-scale=1.0" name="viewport" />',
        f'    <title>{type_name} Datasets</title>',
        '    <link href="https://fonts.googleapis.com/css?family=Open+Sans:300,600" rel="stylesheet" type="text/css" />',
        '    <link href="../../utils/report.css" rel="stylesheet" />',
        '    <script src="https://kit.fontawesome.com/b3ad2626f1.js"></script>',
        '    <style>',
        '        .report-thumb { width: 100%; height: 256px; object-fit: contain; }',
        '        .back-link { text-decoration: none; color: #333; font-weight: 600; display: inline-block; margin-bottom: 1rem; }',
        '        .back-link:hover { color: #007bff; }',
        '    </style>',
        '</head>',
        '<body>',
        '    <div class="content" id="content">',
        '        <a href="../../index.html" class="back-link"><i class="fas fa-arrow-left"></i> Back to Types</a>',
        f'        <h1 class="title">{type_name} Datasets</h1>',
        '        <div class="element-container">'
    ]
    
    for ds_name, thumb_path in datasets_data.items():
        if thumb_path:
            html_lines.append(f'                <div class="report-preview">')
            html_lines.append(f'                    <a href="{ds_name}/index.html">')
            html_lines.append(f'                        <img class="report-thumb" src="{thumb_path}" height="256" width="auto" />')
            html_lines.append(f'                    </a>')
            html_lines.append(f'                    <br/>')
            html_lines.append(f'                    {ds_name}')
            html_lines.append(f'                </div>')
            
    html_lines.extend([
        '        </div>',
        '    </div>',
        '</body>',
        '</html>'
    ])
    
    with open(os.path.join(type_path, 'index.html'), 'w', encoding='utf-8') as f:
        f.write('\n'.join(html_lines))
        
def format_type_name(t):
    mapping = {
        'SwinIR': 'SwinIR',
        'PFT-SR_TSD-SR': 'PFT-SR+TSD-SR',
    }
    return mapping.get(t, t.replace('_', ' '))

def update_root_index(types_data):
    with open(ROOT_INDEX, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    start_index = -1
    end_index = -1
    
    for i, line in enumerate(lines):
        if '<div class="element-container">' in line:
            start_index = i
        if start_index != -1 and 'The interactive viewer template' in line:
            for j in range(i - 1, start_index, -1):
                if '</div>' in lines[j]:
                    end_index = j
                    break
            break
            
    if start_index == -1 or end_index == -1:
        print("Could not find element-container in index.html")
        return

    new_lines = [lines[start_index]]

    for t, thumb in types_data.items():
        type_link = f"{OUTPUT_DIR}/{t}/index.html"
        display_name = format_type_name(t)
        new_lines.append(f'                <div class="report-preview">\n')
        new_lines.append(f'                    <a href="{type_link}" style="text-decoration: none;">\n')
        new_lines.append(f'                        <div style="width:200px; height:256px; display:flex; align-items:center; justify-content:center; text-align:center; background:#f8f9fa; color:#2c3e50; font-size:24px; font-weight:bold; border:2px solid #e9ecef; border-radius:12px; margin-bottom:8px; box-shadow: 0 4px 6px rgba(0,0,0,0.05);">{display_name}</div>\n')
        new_lines.append(f'                    </a>\n')
        new_lines.append(f'                </div>\n')

    new_lines.append('        </div>\n')
    
    final_lines = lines[:start_index] + new_lines + lines[end_index+1:]
    
    with open(ROOT_INDEX, 'w', encoding='utf-8') as f:
        f.writelines(final_lines)
    print(f"Updated {ROOT_INDEX} with {len(types_data)} types.")

def main():
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)

    datasets_dict = extract_info()
    types_data = {}

    for t in TYPES:
        datasets_data = {}
        for ds_name, base_prefixes in sorted(datasets_dict.items()):
            thumb = update_dataset_data(t, ds_name, base_prefixes)
            datasets_data[ds_name] = thumb
            
        update_type_index(t, datasets_data)
        
        type_thumb_for_root = None
        for ds in sorted(datasets_dict.keys()):
            if datasets_data.get(ds):
                root_relative_thumb = datasets_data[ds]
                if root_relative_thumb.startswith("../../"):
                    type_thumb_for_root = root_relative_thumb.replace("../../", "", 1)
                else:
                    type_thumb_for_root = f"{OUTPUT_DIR}/{t}/{root_relative_thumb}"
                break
        
        types_data[t] = type_thumb_for_root
        print(f"Updated type {t} with {len(datasets_dict)} datasets.")
        
    update_root_index(types_data)

if __name__ == "__main__":
    main()
