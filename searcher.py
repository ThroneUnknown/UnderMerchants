import tcod
import json
import itertools
from scraper import scrape


TEXT_KEYS = {
    tcod.event.KeySym.a: 'a',
    tcod.event.KeySym.b: 'b',
    tcod.event.KeySym.c: 'c',
    tcod.event.KeySym.d: 'd',
    tcod.event.KeySym.e: 'e',
    tcod.event.KeySym.f: 'f',
    tcod.event.KeySym.g: 'g',
    tcod.event.KeySym.h: 'h',
    tcod.event.KeySym.i: 'i',
    tcod.event.KeySym.j: 'j',
    tcod.event.KeySym.k: 'k',
    tcod.event.KeySym.l: 'l',
    tcod.event.KeySym.m: 'm',
    tcod.event.KeySym.n: 'n',
    tcod.event.KeySym.o: 'o',
    tcod.event.KeySym.p: 'p',
    tcod.event.KeySym.q: 'q',
    tcod.event.KeySym.r: 'r',
    tcod.event.KeySym.s: 's',
    tcod.event.KeySym.t: 't',
    tcod.event.KeySym.u: 'u',
    tcod.event.KeySym.v: 'v',
    tcod.event.KeySym.w: 'w',
    tcod.event.KeySym.x: 'x',
    tcod.event.KeySym.y: 'y',
    tcod.event.KeySym.z: 'z',
}

WIDTH, HEIGHT = 92, 40
PIXEL_X = WIDTH * 14
PIXEL_Y = HEIGHT * 16
FILE = "underrail.json"

data = ""

cprint = ""
options = []
content = []
coords = [0, 0]
click = False
search = ""
shifted = False
searching = False

names = []
locations = []
categories = []
selling = []
buying = []
special = []
money = []
currencies = []

# Toggle between windowed and fullscreen (PROBABLY TEMPORARY)
def toggle_fullscreen(context):
    if not context.sdl_window_p:
        return
    fullscreen = tcod.lib.SDL_GetWindowFlags(context.sdl_window_p) & (
        tcod.lib.SDL_WINDOW_FULLSCREEN | tcod.lib.SDL_WINDOW_FULLSCREEN_DESKTOP
    )
    tcod.lib.SDL_SetWindowFullscreen(
        context.sdl_window_p,
        0 if fullscreen else tcod.lib.SDL_WINDOW_FULLSCREEN_DESKTOP,
    )

# Main function
def main():
    global cprint
    global coords
    global click
    global searching
    global search
    global shifted
    tileset = tcod.tileset.load_tilesheet(
        "Cooz_curses_14x16.png", 16, 16, tcod.tileset.CHARMAP_CP437
    )
    
    console = tcod.console.Console(WIDTH, HEIGHT, order="F")
    cprint = console.print
    
    get_data()
    
    with tcod.context.new(
       columns=console.width, rows=console.height, tileset=tileset,
    ) as context:
        
        set_screen("Home")
        while True:
            console.clear()
            set_bg((33,34,35))
            
            check_hover(coords)
            
            display()
            context.present(console)
            
            click = False
            for event in tcod.event.get():
                event_tile = context.convert_event(event)
                
                if type(event) == tcod.event.KeyDown:
                    if event.sym == tcod.event.KeySym.LSHIFT or event.sym == tcod.event.KeySym.RSHIFT:
                        shifted = True
                elif type(event) == tcod.event.KeyUp:
                    if event.sym == tcod.event.KeySym.LSHIFT or event.sym == tcod.event.KeySym.RSHIFT:
                        shifted = False
                
                if isinstance(event_tile, tcod.event.MouseMotion):
                    coords = [event_tile.position.x, event_tile.position.y]
                elif isinstance(event, tcod.event.Quit):
                    raise SystemExit()
                
                if searching and type(event) == tcod.event.KeyDown:
                    if event.sym in TEXT_KEYS.keys():
                        if shifted:
                            search += TEXT_KEYS[event.sym].upper()
                        else:
                            search += TEXT_KEYS[event.sym]
                        set_screen("Search")
                        continue
                    elif event.sym == tcod.event.KeySym.BACKSPACE:
                        search = search[:-1]
                        set_screen("Search")
                        continue
                    elif event.sym == tcod.event.KeySym.RETURN:
                        search += "§"
                        set_screen("Search")
                        continue
                match event:
                    case tcod.event.MouseButtonDown(button=button):
                        if button != 1:
                            continue
                        click = True
                    case tcod.event.KeyDown(sym=sym) if sym == tcod.event.KeySym.ESCAPE:
                        raise SystemExit()
                    case tcod.event.KeyDown(sym=sym) if sym == tcod.event.KeySym.h:
                        set_screen("Home")
                    case tcod.event.KeyDown(sym=sym) if sym == tcod.event.KeySym.s:
                        set_screen("Search")
                    case tcod.event.KeyDown(sym=sym) if sym == tcod.event.KeySym.a:
                        set_screen("All")
                    case tcod.event.KeyDown(sym=sym) if sym == tcod.event.KeySym.c:
                        set_screen("Category")
                    case tcod.event.KeyDown(sym=sym) if sym == tcod.event.KeySym.b:
                        set_screen("Buys")
                    case tcod.event.KeyDown(sym=sym) if sym == tcod.event.KeySym.l:
                        set_screen("Location")
                    case tcod.event.KeyDown(sym=sym) if sym == tcod.event.KeySym.u:
                        set_screen("Currency")

def set_bg(color):
    for i in range(HEIGHT): 
        cprint(0, i, "".join([" " for j in range(WIDTH)]), bg=color)

def set_screen(screen):
    global options
    global content
    global searching
    global search
    x = 4
    y = 4
    options = []
    content = []
    
    if screen == "Home":
        set_bg((33,34,35))
        content.append(new_content(2, 1, "Sort By:"))
        content.append(new_content(1, 2, line("─", 20), (174,87,0)))
        options.append(new_option(2,3,"[A] All", set_screen, "All"))
        options.append(new_option(2,4,"[L] Location", set_screen, "Location"))
        options.append(new_option(2,5,"[C] Category", set_screen, "Category"))
        options.append(new_option(2,6,"[B] Buys", set_screen, "Buys"))
        options.append(new_option(2,7,"[S] Search", set_screen, "Search"))
        options.append(new_option(2,8,"[U] Currency", set_screen, "Currency"))
    
    # List all merchants by name
    elif screen == "All":
        set_bg((33,34,35))
        content.append(new_content(2, 1, screen[:]))
        content.append(new_content(1, 2, line("─", 20), (174,87,0)))
        options.append(new_option(WIDTH - 9, 1, "[H] Home", set_screen, "Home"))
        
        content.append(new_content(2, 1, "All Merchants"))
        content.append(new_content(1, 2, line("─", 20), (174,87,0)))
        
        x = 2
        y = 3
        
        # List all names
        for i in range(len(names)):
            if y > HEIGHT - 2:
                y = 3
                x += 30
            options.append(new_option(x,y,names[i], set_screen, names[i]))
            y += 1
    
    # Show available categories
    elif screen == "Category":
        set_screen("Home")
        content.append(new_content(14, 5, "──", (174,87,0)))
        
        x = 16
        y = 3
        
        for i in range(len(categories)):
            options.append(new_option(x,y,f"{categories[i]} ({sum([1 for x in data if x['CATEGORY'] == categories[i]])})",set_screen,categories[i]))
            y += 1
    
    # Show available locations
    elif screen == "Location":
        set_screen("Home")
        content.append(new_content(14, 4, "──", (174,87,0)))
        
        x = 16
        y = 3
        
        for i in range(len(locations)):
            options.append(new_option(x,y,f"{locations[i]} ({sum([1 for x in data if x['LOCATION'] == locations[i]])})",set_screen,locations[i]))
            y += 1
    
    # Show available currencies
    elif screen == "Currency":
        set_screen("Home")
        content.append(new_content(14, 8, "──", (174,87,0)))
        
        x = 16
        y = 6
        
        for i in range(len(currencies)):
            options.append(new_option(x,y,f"{currencies[i]} ({sum([1 for x in data if currencies[i] in x['CURRENCIES']])})",set_screen,currencies[i]))
            y += 1
    
    # Show available items that merchants will buy
    elif screen == "Buys":
        set_bg((33,34,35))
        content.append(new_content(2, 1, screen[:]))
        content.append(new_content(1, 2, line("─", 20), (174,87,0)))
        options.append(new_option(WIDTH - 9, 1, "[H] Home", set_screen, "Home"))
        
        content.append(new_content(2, 1, "Items merchants buy"))
        content.append(new_content(1, 2, line("─", 20), (174,87,0)))
        
        x = 2
        y = 3
        
        # List all items being bought
        for i in range(len(buying)):
            if y > HEIGHT - 2:
                y = 3
                x += 30
            if len(buying[i]) > 29:
                options.append(new_option(x,y,buying[i][:26]+"...", set_screen, buying[i]))
            else:
                options.append(new_option(x,y,buying[i], set_screen, buying[i]))
            y += 1
    
    # Search for items to purchase
    elif screen == "Search":
        set_screen("Home")
        content.append(new_content(12, 7, ": "))
        
        searching = True
        
        if len(search) > 0  and search[-1] == "§":
            searching = False
            set_screen("SEARCH§"+search[:-1])
            search = ""
        else:
            content.append(new_content(13, 7, search, (5, 168, 232)))
    
    # Show all merchants of a category
    elif screen in categories:
        set_bg((33,34,35))
        content.append(new_content(2, 1, f"Category: {screen[:]}"))
        content.append(new_content(1, 2, line("─", 20), (174,87,0)))
        options.append(new_option(WIDTH - 9, 1, "[H] Home", set_screen, "Home"))
        
        merchant_list = [x["NAME"] for x in data if x["CATEGORY"] == screen]
        
        x = 2
        y = 3
        
        # List names
        for i in range(len(merchant_list)):
            if y > HEIGHT - 2:
                y = 3
                x += 30
            for entry in data:
                if merchant_list[i] == entry["NAME"]:
                    json_data = entry
            options.append(new_option(x,y,f"{merchant_list[i]} ({json_data['LOCATION']})", set_screen, merchant_list[i]))
            y += 1
    
    # Show all merchants of a location
    elif screen in locations:
        set_bg((33,34,35))
        content.append(new_content(2, 1, f"Location: {screen[:]}"))
        content.append(new_content(1, 2, line("─", 20), (174,87,0)))
        options.append(new_option(WIDTH - 9, 1, "[H] Home", set_screen, "Home"))
    
        merchant_list = [x["NAME"] for x in data if x["LOCATION"] == screen]
        
        x = 2
        y = 3
        
        # List names
        for i in range(len(merchant_list)):
            if y > HEIGHT - 2:
                y = 3
                x += 30
            for entry in data:
                if merchant_list[i] == entry["NAME"]:
                    json_data = entry
            options.append(new_option(x,y,f"{merchant_list[i]} ({json_data['CATEGORY']})", set_screen, merchant_list[i]))
            y += 1
    
    # Show all merchants with a currency
    elif screen in currencies:
        set_bg((33,34,35))
        content.append(new_content(2, 1, screen[:]))
        content.append(new_content(1, 2, line("─", 20), (174,87,0)))
        options.append(new_option(WIDTH - 9, 1, "[H] Home", set_screen, "Home"))
    
        merchant_list = [x["NAME"] for x in data if screen in x["CURRENCIES"]]
        content.append(new_content(2, 1, f"Currency: {screen}"))
        content.append(new_content(1, 2, line("─", 20), (174,87,0)))
        
        x = 2
        y = 3
        
        # List names
        for i in range(len(merchant_list)):
            if y > HEIGHT - 2:
                y = 3
                x += 30
            for entry in data:
                if merchant_list[i] == entry["NAME"]:
                    json_data = entry
            options.append(new_option(x,y,f"{merchant_list[i]} ({json_data['MONEY'][json_data['CURRENCIES'].index(screen)]})", set_screen, merchant_list[i]))
            y += 1
    
    # Show all merchants buying a certain item
    elif screen in buying:
        set_bg((33,34,35))
        content.append(new_content(2, 1, screen[:]))
        content.append(new_content(1, 2, line("─", 20), (174,87,0)))
        options.append(new_option(WIDTH - 9, 1, "[H] Home", set_screen, "Home"))
        
        merchant_list = [x["NAME"] for x in data if screen in clean_list(x["BUYING"])]
        
        x = 2
        y = 3
        
        # List names
        for i in range(len(merchant_list)):
            if y > HEIGHT - 2:
                y = 3
                x += 30
            for entry in data:
                if merchant_list[i] == entry["NAME"]:
                    json_data = entry
            options.append(new_option(x,y,f"{merchant_list[i]} ({json_data['LOCATION']})", set_screen, merchant_list[i]))
            y += 1
    
    # Show profile of merchant
    elif screen in names:
        for entry in data:
            if screen in entry["NAME"]:
                json_data = entry
        set_bg((33,34,35))
        content.append(new_content(2, 1, screen[:]))
        content.append(new_content(1, 2, line("─", 20), (174,87,0)))
        options.append(new_option(WIDTH - 9, 1, "[H] Home", set_screen, "Home"))
        
        # Show basic information
        content.append(new_content(2, 3, "Location:"))
        options.append(new_option(12, 3, json_data["LOCATION"], set_screen, json_data["LOCATION"]))
        content.append(new_content(2, 4, "Category:"))
        options.append(new_option(12, 4, json_data["CATEGORY"], set_screen, json_data["CATEGORY"]))
        
        # Show available funds
        content.append(new_content(32, 3, "Money:"))
        for i in range(len(json_data["MONEY"])):
            content.append(new_content(39, 3+i, str(json_data["MONEY"][i])))
            content.append(new_content(42, 3+i, str(json_data["CURRENCIES"][i])))
        
        x=2
        y=7
        
        # Show items for sale
        content.append(new_content(1, 6, "Notable Items for sale:"))
        for i in range(len(json_data["SELLING"])):
            if y > HEIGHT - 2:
                content.append(new_content(x, y, "NOT ALL ITEMS SHOWN"))
                break
            if len(json_data["SELLING"][i]) > 29:
                content.append(new_content(x,y,json_data["SELLING"][i][:26] + "...", (5, 168, 232)))
            else:
                content.append(new_content(x,y,json_data["SELLING"][i], (5, 168, 232)))
            y += 1
        
        vline(31, 6, max(len(json_data["SELLING"]), len(json_data["BUYING"]))+1)
        
        x=33
        y=7
        
        # Show items looking to buy
        content.append(new_content(32,6, "Looking to buy:"))
        for i in range(len(json_data["BUYING"])):
            if y > HEIGHT:
                content.append(new_content(x, y, "NOT ALL ITEMS SHOWN"))
                break
            if len(json_data["BUYING"][i]) > 28:
                options.append(new_option(x,y,json_data["BUYING"][i][:25] + "...", set_screen, json_data["BUYING"][i]))
            else:
                options.append(new_option(x,y,json_data["BUYING"][i], set_screen, clean_list([json_data["BUYING"][i]])[0]))
            y += 1
        
        y = 7 + len(json_data["SELLING"]) + 2
        x = 2
        
        # Show special items (if any)
        if json_data["SPECIAL"] != []:
            content.append(new_content(1,y-1, "Special inventory:"))
            for i in range(len(json_data["SPECIAL"])):
                if y > HEIGHT - 2:
                    content.append(new_content(x, y, "NOT ALL ITEMS SHOWN"))
                    break
                if len(json_data["SPECIAL"][i]) > 29:
                    content.append(new_content(x,y,json_data["SPECIAL"][i][:26] + "...", (5, 168, 232)))
                else:
                    content.append(new_content(x,y,json_data["SPECIAL"][i], (5, 168, 232)))
                y += 1
    
    # Search for something
    elif "SEARCH§" in screen:
        set_bg((33,34,35))
        content.append(new_content(2, 1, "Search Results"))
        content.append(new_content(1, 2, line("─", 20), (174,87,0)))
        options.append(new_option(WIDTH - 9, 1, "[H] Home", set_screen, "Home"))
        
        usersearch = screen.split("§")[1].lower()
        
        x = 3
        y = 4
        
        # Category Results
        content.append(new_content(2, 3, "Categories"))
        for i in range(len(categories)):
            if y > HEIGHT - 2:
                y = 4
                vline(x+28, 4, HEIGHT  - 6)
                x += 30
            if usersearch in categories[i].lower():
                if len(f"{categories[i]} ({sum([1 for x in data if x['CATEGORY'] == categories[i]])})") > 28:
                    options.append(new_option(x,y,f"{categories[i][:21]}... ({sum([1 for x in data if x['CATEGORY'] == categories[i]])})",set_screen,categories[i]))
                else:
                    options.append(new_option(x,y,f"{categories[i]} ({sum([1 for x in data if x['CATEGORY'] == categories[i]])})",set_screen,categories[i]))
                y += 1
        
        # Location Results
        y += 1
        if y > HEIGHT - 2:
            y = 4
            vline(x+28, 4, HEIGHT  - 6)
            x += 30
        content.append(new_content(x-1, y, "Locations"))
        y += 1
        for i in range(len(locations)):
            if y > HEIGHT - 2:
                y = 4
                x += 30
                vline(x+28, 4, HEIGHT  - 6)
            if usersearch in locations[i].lower():
                if len(f"{locations[i]} ({sum([1 for x in data if x['LOCATION'] == locations[i]])})") > 28:
                    options.append(new_option(x,y,f"{locations[i][:20]}... ({sum([1 for x in data if x['LOCATION'] == locations[i]])})",set_screen,locations[i]))
                else:
                    options.append(new_option(x,y,f"{locations[i]} ({sum([1 for x in data if x['LOCATION'] == locations[i]])})",set_screen,locations[i]))
                y += 1
        
        # Names Results
        y += 1
        if y > HEIGHT - 2:
            y = 4
            vline(x+28, 4, HEIGHT  - 6)
            x += 30
        content.append(new_content(x-1, y, "Names"))
        y += 1
        for i in range(len(names)):
            if y > HEIGHT - 2:
                y = 4
                vline(x+28, 4, HEIGHT  - 6)
                x += 30
            if usersearch in names[i].lower():
                if len(f"{names[i]} ({sum([1 for x in data if x['NAME'] == names[i]])})") > 28:
                    options.append(new_option(x,y,f"{names[i][:20]}... ({sum([1 for x in data if x['NAME'] == names[i]])})",set_screen,names[i]))
                else:
                    options.append(new_option(x,y,f"{names[i]} ({sum([1 for x in data if x['NAME'] == names[i]])})",set_screen,names[i]))
                y += 1
        
        # Buys Results
        y += 1
        if y > HEIGHT - 2:
            y = 4
            vline(x+28, 4, HEIGHT  - 6)
            x += 30
        content.append(new_content(x-1, y, "Merchants Buying"))
        y += 1
        for i in range(len(buying)):
            if y > HEIGHT - 2:
                y = 4
                vline(x+28, 4, HEIGHT  - 6)
                x += 30
            if usersearch in buying[i].lower():
                if len(f"{buying[i]} ({sum([1 for x in data if x['BUYING'] == buying[i]])})") > 28:
                    options.append(new_option(x,y,f"{buying[i][:20]}... ({sum([1 for x in data if buying[i] in clean_list(x['BUYING'])])})",set_screen,buying[i]))
                else:
                    options.append(new_option(x,y,f"{buying[i]} ({sum([1 for x in data if buying[i] in clean_list(x['BUYING'])])})",set_screen,buying[i]))
                y += 1

def vline(x, y, height, char="│", fg=(174,87,0), bg=(32,33,34)):
    for i in range(height):
        content.append(new_content(x,y+i,char,fg,bg))

def check_hover(coords):
    global options
    global click
    for i in range(len(options)):
        if coords[0] in range(options[i]["x"], options[i]["x"] + len(options[i]["text"])) and options[i]["y"] == coords[1]:
            options[i]["hover"] = True
            if click:
                click = False
                options[i]["on_click"](options[i]["parameter"])
                return None
        else:
            options[i]["hover"] = False

def display():
    for option in options:
        if option["hover"]:
            cprint(option["x"], option["y"], option["text"], (226, 113, 0), (32,33,34))
        else:
            cprint(option["x"], option["y"], option["text"], (174, 87, 0), (32,33,34))
    for text in content:
        cprint(text["x"], text["y"], text["text"], text["fg"], text["bg"])

line = lambda char, length: "".join(char for i in range(length))

new_option = lambda x, y, text, onclick, parameter : {"x":x, "y":y, "text":text, "on_click":onclick, "parameter":parameter, "hover":False}
new_content = lambda x, y, text, fg=(170,170,170), bg=(32,33,34) : {"x":x, "y":y, "text":text, "fg":fg, "bg":bg}

def clean_list(l):
    new_list = sorted(list(set(list(l))))[:]
    removal = (" ", "")
    sub_removal = (" (always)", " (Always)", " (rare)", " (rarely)", "\xa0E", " §", "§")
    for item in removal:
        if item in new_list:
            new_list.remove(item[:])
    for i in range(len(new_list)):
        for item in sub_removal:
            new_list[i] = "".join(str(new_list[i]).split(item))
    return sorted(list(set(new_list)))

# Rescrape web data, 'nothing' parameter exists as placeholder for option
def get_data(nothing=""):
    global data
    global names
    global locations
    global categories
    global selling
    global buying
    global special
    global money
    global currencies
    
    with open(FILE, "r") as f:
        data = json.loads(f.read())
        
    names = clean_list([x["NAME"] for x in data])
    locations = clean_list([x["LOCATION"] for x in data])
    categories = clean_list([x["CATEGORY"] for x in data])
    selling = clean_list(itertools.chain.from_iterable([x["SELLING"] for x in data]))
    buying = clean_list([str(y) + "§" for y in itertools.chain.from_iterable([x["BUYING"] for x in data])])
    special = clean_list(itertools.chain.from_iterable([x["SPECIAL"] for x in data]))
    money = clean_list(itertools.chain.from_iterable([x["MONEY"] for x in data]))
    currencies = clean_list(itertools.chain.from_iterable([x["CURRENCIES"] for x in data]))

if __name__ == "__main__":
    main()