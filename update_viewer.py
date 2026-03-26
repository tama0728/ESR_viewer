import os
import json
import re

OUTPUT_DIR = 'output_images'
SR_DIR = 'SR'
MODELS_DIR = 'models'
ROOT_INDEX = 'index.html'

# Explicit sorting order and filter list
PRIORITY = [
    'LR', 'HR', 'SwinIR-C', 'PFT', 'SwinIR-RW', 
    'Adc-SR', 'TSD_SR', 'edge', 'histo', 'edge_histo', 'face_histo', 'final'
]

def get_image_files(directory):
    valid_extensions = {'.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp'}
    images = []
    if not os.path.exists(directory):
        return images
    for f in os.listdir(directory):
        if os.path.splitext(f)[1].lower() in valid_extensions:
            images.append(f)
    return images

def get_model_folder_name(model_key, dataset_name):
    """Maps the model key to its actual folder prefix/name in the models directory."""
    mapping = {
        'SwinIR-C': f"SwinIR-C/swinir_classical_sr_x4_{dataset_name}",
        'PFT': f"PFT/PFT_{dataset_name}",
        'SwinIR-RW': f"SwinIR-RW/swinir_real_sr_x4_{dataset_name}",
        'Adc-SR': f"Adc_SR/AdcSR_{dataset_name}",
        'TSD_SR': f"TSD_SR/{dataset_name}"
    }
    return mapping.get(model_key, "")

def update_dataset_data(type_name, dataset_name):
    """Generates data.js and index.html for a specific dataset within a type."""
    dataset_path = os.path.join(OUTPUT_DIR, type_name, dataset_name)
    
    # 1. output_images categories
    categories_available = []
    if os.path.exists(dataset_path):
        for d in os.listdir(dataset_path):
            if os.path.isdir(os.path.join(dataset_path, d)):
                if d in PRIORITY:
                    categories_available.append(d)

    image_map = {} # basename -> {category: filepath}
    
    def get_pure_basename(img_filename):
        img_base = os.path.splitext(img_filename)[0]
        if img_base in image_map:
            return img_base
        for b in image_map:
            if img_base.startswith(b + '_') or img_base.startswith(b + 'x'):
                return b
        return img_base

    # Collect from output_images (usually pure basenames)
    for cat in categories_available:
        cat_path = os.path.join(dataset_path, cat)
        images = get_image_files(cat_path)
        for img in images:
            basename = get_pure_basename(img)
            if basename not in image_map:
                image_map[basename] = {}
            image_map[basename][cat] = f"{cat}/{img}"

    # 2. Collect HR and LR from SR/<dataset>/
    sr_dataset_path = os.path.join(SR_DIR, dataset_name)
    if os.path.exists(sr_dataset_path):
        # HR (usually pure)
        hr_path = os.path.join(sr_dataset_path, "HR")
        if os.path.exists(hr_path):
            for img in get_image_files(hr_path):
                basename = get_pure_basename(img)
                if basename not in image_map:
                    image_map[basename] = {}
                image_map[basename]['HR'] = f"../../../{SR_DIR}/{dataset_name}/HR/{img}"
        
        # LR (check 'LR_bicubic' or 'LR')
        lr_base_path = os.path.join(sr_dataset_path, "LR_bicubic")
        lr_rel = "LR_bicubic"
        if not os.path.exists(lr_base_path):
            lr_base_path = os.path.join(sr_dataset_path, "LR")
            lr_rel = "LR"
            
        lr_path = lr_base_path
        if os.path.exists(os.path.join(lr_base_path, "X4")):
            lr_path = os.path.join(lr_base_path, "X4")
            lr_rel = f"{lr_rel}/X4"
            
        if os.path.exists(lr_path):
            lr_images = get_image_files(lr_path)
            print(f"Found {len(lr_images)} LR images in {lr_path}")
            for img in lr_images:
                basename = get_pure_basename(img)
                if basename not in image_map:
                    image_map[basename] = {}
                image_map[basename]['LR'] = f"../../../{SR_DIR}/{dataset_name}/{lr_rel}/{img}"

    # 3. Collect from models
    for model_cat in ['SwinIR-C', 'PFT', 'SwinIR-RW', 'Adc-SR', 'TSD_SR']:
        model_subpath = get_model_folder_name(model_cat, dataset_name)
        model_dir = os.path.join(MODELS_DIR, model_subpath)
        if os.path.exists(model_dir):
            for img in get_image_files(model_dir):
                basename = get_pure_basename(img)
                if basename not in image_map:
                    image_map[basename] = {}
                image_map[basename][model_cat] = f"../../../{MODELS_DIR}/{model_subpath}/{img}"

    # Construct data object enforcing strict priority
    image_boxes = []
    sorted_basenames = sorted(image_map.keys())
    
    for basename in sorted_basenames:
        elements = []
        for cat in PRIORITY:
            # Filter models according to the parent folder type
            if cat in ['SwinIR-C', 'PFT', 'SwinIR-RW', 'Adc-SR', 'TSD_SR']:
                if type_name == 'SwinIR' and cat not in ['SwinIR-C', 'SwinIR-RW']:
                    continue
                if type_name == 'PFT_AdcSR' and cat not in ['PFT', 'Adc-SR']:
                    continue
                if type_name == 'TSD_SR_PFT' and cat not in ['PFT', 'TSD_SR']:
                    continue
                if type_name == 'TSD_SR_SwinIR' and cat not in ['SwinIR-C', 'TSD_SR']: # Defaulting to SwinIR-C for SwinIR models
                    continue

            if cat in image_map[basename]:
                el = {
                    "title": cat,
                    "version": "-",
                    "image": image_map[basename][cat]
                }
                if cat == 'LR':
                    el["scale"] = 4
                elements.append(el)
        
        if elements:
            image_boxes.append({
                "title": basename,
                "elements": elements
            })

    # Write data.js
    if not os.path.exists(dataset_path):
        os.makedirs(dataset_path)

    data_content = f"const data = \n{json.dumps({'imageBoxes': image_boxes}, indent=4)}\n"
    with open(os.path.join(dataset_path, 'data.js'), 'w', encoding='utf-8') as f:
        f.write(data_content)
        
    # Write dataset index.html
    dataset_html = f"""<!DOCTYPE doctype html>
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
        // new ChartBox(content, data["stats"]);
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
    with open(os.path.join(dataset_path, 'index.html'), 'w', encoding='utf-8') as f:
        f.write(dataset_html)
    
    if image_boxes and image_boxes[0]['elements']:
        first_img = image_boxes[0]['elements'][0]['image']
        if first_img.startswith("../../../"):
            return first_img.replace("../../../", "../../", 1)
        else:
            return f"{dataset_name}/{first_img}"
    return None

def update_type_index(type_name, datasets_data):
    """Generates the index.html for a specific type listing its datasets."""
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
        'PFT_AdcSR': 'PFT+AdcSR',
        'SwinIR': 'SwinIR',
        'TSD_SR_PFT': 'PFT+TSD_SR',
        'TSD_SR_SwinIR': 'SwinIR+TSD_SR'
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
        print(f"Directory {OUTPUT_DIR} not found.")
        return

    types = [d for d in os.listdir(OUTPUT_DIR) if os.path.isdir(os.path.join(OUTPUT_DIR, d))]
    custom_order = ['SwinIR', 'PFT_AdcSR', 'TSD_SR_SwinIR', 'TSD_SR_PFT']
    types.sort(key=lambda x: custom_order.index(x) if x in custom_order else 999)
    
    types_data = {}
    
    for t in types:
        type_path = os.path.join(OUTPUT_DIR, t)
        datasets = [d for d in os.listdir(type_path) if os.path.isdir(os.path.join(type_path, d))]
        datasets.sort()
        
        datasets_data = {}
        for ds in datasets:
            thumb = update_dataset_data(t, ds)
            datasets_data[ds] = thumb
            
        update_type_index(t, datasets_data)
        
        type_thumb_for_root = None
        for ds in datasets:
            if datasets_data[ds]:
                root_relative_thumb = datasets_data[ds]
                if root_relative_thumb.startswith("../../"):
                    type_thumb_for_root = root_relative_thumb.replace("../../", "", 1)
                else:
                    type_thumb_for_root = f"{OUTPUT_DIR}/{t}/{root_relative_thumb}"
                break
        
        types_data[t] = type_thumb_for_root
        print(f"Updated type {t} with {len(datasets)} datasets.")
        
    update_root_index(types_data)

if __name__ == "__main__":
    main()
