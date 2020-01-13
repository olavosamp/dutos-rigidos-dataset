
# String class codes  used in json files
tags = [ "anodo", "dano-duvida", "dano", "duto", "variacao", "metal", "planta", "sucata", "peixe", "nada" ]

event_tags = [ "anodo", "dano-duvida", "dano", "variacao", "metal", "planta", "sucata", "peixe" ]

alteration_tags = [ "anodo", "dano-duvida", "dano", "variacao", "nada" ]

clean_duct_tag = "duto"

clean_duct_frame_rate = 1

confusion_time = 1

petro_class_table = [
                     "dano",    # Position in list equates to translation priority
                     "anodo",   # index 0 is highest priority, last index is lowest
                     "sucata",  #
                     "cruz",    #
                     "algas",   #
                     "duto",    #
                     "peixe",
                     "variacao"
]

class_priority_table = petro_class_table.copy()

UNUSED_CLASS = "UNUSED_CLASS"

class_translation_table = {
                            petro_class_table[0]:      ["dano", "dano-duvida"],
                            petro_class_table[1]:      ["anodo"],
                            petro_class_table[2]:      ["metal", "sucata"],
                            petro_class_table[4]:      ["planta"],
                            petro_class_table[5]:      ["duto"],
                            petro_class_table[6]:      ["peixe"],
                            petro_class_table[7]:      ["variacao"],
                            # UNUSED_CLASS:              "nada",
}

# Videos formats supported by the package
#video_formats = [ "mp4" ]
