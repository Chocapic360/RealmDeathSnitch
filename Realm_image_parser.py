from PIL import Image
import os
import shutil

def item_image_parser(x,y,itemname):
    im = Image.open("./images/renders.png")

    left = x
    top = y
    right = x + 40
    bottom = y + 40

    im1 = im.crop((left, top, right, bottom))
    os.makedirs("./itempics", exist_ok=True)
    im1.save(f"./itempics/{itemname}.png")

def skin_image_parser(x,y,playername):
    im = Image.open("./images/sheets.png")

    left = x
    top = y - 250
    right = x + 50
    bottom = y - 200

    im1 = im.crop((left, top, right, bottom))
    os.makedirs("./skinpics", exist_ok=True)
    im1.save(f"./skinpics/{playername}.png")

def death_image_combiner(death_dict:dict):
    template = Image.open("./images/image-template.png")
    skin = Image.open(f"./skinpics/{death_dict['player-name']}.png")
    combined = Image.new('RGBA', (template.width, template.height), (0, 0, 0, 0))
    combined.paste(template, (0, 0), template)
    for i in range(len(death_dict['equipment'])):
        item = Image.open(f"./itempics/{death_dict['equipment'][i]['name']}.png")
        combined.paste(item, (60 + (45 * i), 12), item)
    combined.paste(skin, (6, 7), skin)
    combined.resize((combined.width * 2, combined.height * 2))
    combined.save("./images/output.png")

def character_image_combiner(character_dict:dict, index:int):
    template = Image.open("./images/image-template.png")
    # Naming scheme for sin pics is class_index.png
    skin = Image.open(f"./skinpics/{character_dict['class']}_{index}.png")
    combined = Image.new('RGBA', (template.width, template.height), (0, 0, 0, 0))
    combined.paste(template, (0, 0), template)
    for i in range(len(character_dict['equipment'])):
        item = Image.open(f"./itempics/{character_dict['equipment'][i]['name']}.png")
        combined.paste(item, (60 + (45 * i), 12), item)
    combined.paste(skin, (6, 7), skin)
    combined.resize((combined.width * 2, combined.height * 2))
    combined.save("./images/alive_output.png")

def delete_all_files_in_folder(folder_path):
    for filename in os.listdir(folder_path):
        file_path = os.path.join(folder_path, filename)
        try:
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.unlink(file_path)
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)
        except Exception as e:
            print(f'Failed to delete {file_path}. Reason: {e}')
