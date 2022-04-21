########################################################################################
#                                                                                      #
#  JSON converter for Anatolia Mud area files                                          #
#  github.com/ozgyilmaz/Anatolia-MUD-area-to-JSON-converter                            #
#                                                                                      #
#  Inspired by maplechori's "parse ewar" (github.com/maplechori/parse_ewar)            #
#  Written by Ozgur Yilmaz (github.com/ozgyilmaz)                                      #
#                                                                                      #
#  The project consists of a python file and highly using pyparsing module.            #
#  The python script easily converts a standard Anatolia MUD area file to a JSON file. #
#                                                                                      #
#  There are some exceptions and failures:                                             #
#  social.are is beyond the scope. At least for now...                                 #
#                                                                                      #
#  Usage:                                                                              #
#  python are-to-json.py <area_name_without_extension>                                 #
#                                                                                      #
#  Example:                                                                            #
#  python are-to-json.py under2                                                        #
#  python are-to-json.py help                                                          #
#  python are-to-json.py midgaard                                                      #
#                                                                                      #
########################################################################################

from pyparsing import *

import argparse
import json
import os
import re

space               = White(' ',exact=1)
# read everything till a tilde.
tilde_string        = Combine(Regex("[^~]*") + Suppress(Literal("~")))
vnum                = Suppress(Literal("#")) + Word(nums).setResultsName("vnum") + Suppress(restOfLine)
asterisk_comment    = Regex("[\*].*")


area_grammar        =   Suppress(Literal("#AREA")) +\
                        tilde_string.setResultsName('file') + Suppress(restOfLine) +\
                        tilde_string.setResultsName('name') + Suppress(restOfLine) +\
                        Combine(
                                Suppress("{") +\
                                ZeroOrMore(Suppress(space)) +\
                                Word(nums)
                                ).setResultsName('low_range') +\
                        Combine(
                                Word(nums) +\
                                ZeroOrMore(Suppress(space)) +\
                                Suppress("}")
                                ).setResultsName('high_range') +\
                        Word(alphanums).setResultsName('writer') +\
                        tilde_string.setResultsName('credits') + Suppress(restOfLine) +\
                        Word(nums).setResultsName('min_vnum') +\
                        Word(nums).setResultsName('max_vnum') + Suppress(restOfLine)

room_grammar        =   Suppress(Literal("#ROOMS")) +\
                        ZeroOrMore(
                            Group(
                                vnum +\
                                tilde_string.setResultsName('name') + Suppress(restOfLine) +\
                                tilde_string.setResultsName('description') + Suppress(restOfLine) +\
                                Suppress(Word(nums)) +\
                                Word(alphanums+"|"+"-").setResultsName('flags') +\
                                Word("-"+nums).setResultsName('sector') + Suppress(restOfLine) &\
                                ZeroOrMore(
                                    (Suppress(Literal("H")) + Word(nums)).setResultsName('heal_rate') |
                                    (Suppress(Literal("M")) + Word(nums)).setResultsName('mana_rate')|
                                    (Suppress(Literal("O")) + tilde_string).setResultsName('owner') |
                                    Group(
                                        Suppress(Literal("E")) +\
                                        tilde_string.setResultsName('keyword') +\
                                        tilde_string.setResultsName('description')
                                    ).setResultsName('extra_descriptions*') |
                                    Group(
                                        Combine(
                                            Literal("D") +\
                                            Word(nums)
                                        ).setResultsName('exit_door') +\
                                        tilde_string.setResultsName('exit_description') +\
                                        tilde_string.setResultsName('exit_keyword') +\
                                        Word(nums).setResultsName('exit_locks') +\
                                        Word("-" + nums).setResultsName('exit_key') +\
                                        Word("-" +nums).setResultsName('exit_u1_vnum')
                                    ).setResultsName('exits*')
                                ) +\
                                Suppress(Literal("S"))
                            )
                        ) + Suppress(Literal("#0"))
                  
object_grammar      =   Suppress(Literal("#OBJECTS")) +\
                        ZeroOrMore(
                            Group(
                                vnum +\
                                tilde_string.setResultsName('name') + Suppress(restOfLine) +\
                                tilde_string.setResultsName('short_description') + Suppress(restOfLine) +\
                                tilde_string.setResultsName('description') + Suppress(restOfLine) +\
                                tilde_string.setResultsName('material') + Suppress(restOfLine) +\
                                Word(alphanums+"_"+"-").setResultsName('type') +\
                                Word(alphanums+"|").setResultsName('extra_flags') +\
                                Word(alphanums+"|").setResultsName('wear_flags') + Suppress(restOfLine) +\
                                Word(alphanums+" "+"'"+"-").setResultsName('values') +\
                                Word("-"+nums).setResultsName('level') +\
                                Word("-"+nums).setResultsName('weight') +\
                                Word("-"+nums).setResultsName('cost') +\
                                Word(alphanums).setResultsName('condition') + Suppress(restOfLine) +\
                                ZeroOrMore(
                                    Group(
                                        Suppress(Literal("A")) +\
                                        Word("-"+nums).setResultsName('location') +\
                                        Word("-"+nums).setResultsName('modifier')
                                    ).setResultsName('affects_a*') |
                                    Group(
                                        Suppress(Literal("F")) +\
                                        Word(alphas).setResultsName('where') +\
                                        Word(nums).setResultsName('location') +\
                                        Word("-"+nums).setResultsName('modifier') +\
                                        Word(alphanums).setResultsName('bitvector')
                                    ).setResultsName('affects_f*') |
                                    Group(
                                        Suppress(Literal("E")) +\
                                        tilde_string.setResultsName('keyword') +\
                                        tilde_string.setResultsName('description')
                                    ).setResultsName('extra_descriptions*')
                                )
                            )
                        ) + Suppress(Literal("#0"))

old_object_grammar  =   Suppress(Literal("#OBJOLD")) +\
                        ZeroOrMore(
                            Group(
                                vnum +\
                                tilde_string.setResultsName('name') +\
                                tilde_string.setResultsName('short_description') +\
                                tilde_string.setResultsName('description') +\
                                Suppress(tilde_string) +\
                                Word(alphanums).setResultsName('type') +\
                                Word(alphanums+"|").setResultsName('extra_flags') +\
                                Word(alphanums+"|").setResultsName('wear_flags') +\
                                Word(alphanums+" "+"'"+"-").setResultsName('values') +\
                                Word(nums).setResultsName('weight') +\
                                Word(nums).setResultsName('cost') +\
                                Suppress(Word(nums)) +\
                                ZeroOrMore(
                                    Group(
                                        Suppress(Literal("A")) +\
                                        Word("-"+nums).setResultsName('location') +\
                                        Word("-"+nums).setResultsName('modifier')
                                    ).setResultsName('affects_a*') |
                                    Group(
                                        Suppress(Literal("E")) +\
                                        tilde_string.setResultsName('keyword') +\
                                        tilde_string.setResultsName('description')
                                    ).setResultsName('extra_descriptions*')
                                )
                            )
                        ) + Suppress(Literal("#0"))

mobile_grammar      =   Suppress(Literal("#MOBILES")) +\
                        ZeroOrMore(
                            Group(
                                vnum +\
                                tilde_string.setResultsName('name') + Suppress(restOfLine) +\
                                tilde_string.setResultsName('short_description') + Suppress(restOfLine) +\
                                tilde_string.setResultsName('long_description') + Suppress(restOfLine) +\
                                tilde_string.setResultsName('description') + Suppress(restOfLine) +\
                                tilde_string.setResultsName('race') + Suppress(restOfLine) +\
                                Word(alphanums+"|").setResultsName('act') +\
                                Word(alphanums+"|").setResultsName('affected_by') +\
                                Word(nums+"-").setResultsName('alignment') +\
                                Word(nums).setResultsName('group') + Suppress(restOfLine) +\
                                Word(nums).setResultsName('level') +\
                                Word(nums+"-").setResultsName('hitroll') +\
                                Word(alphanums+"+").setResultsName('hit_dice') +\
                                Word(alphanums+"+").setResultsName('mana_dice') +\
                                Word(alphanums+"+").setResultsName('dam_dice') +\
                                Word(alphanums).setResultsName('dam_type') + Suppress(restOfLine) +\
                                Word(nums+"-").setResultsName('ac_pierce') +\
                                Word(nums+"-").setResultsName('ac_bash') +\
                                Word(nums+"-").setResultsName('ac_slash') +\
                                Word(nums+"-").setResultsName('ac_exotic') + Suppress(restOfLine) +\
                                Word(alphanums).setResultsName('off_flags') +\
                                Word(alphanums).setResultsName('imm_flags') +\
                                Word(alphanums).setResultsName('res_flags') +\
                                Word(alphanums).setResultsName('vuln_flags') + Suppress(restOfLine) +\
                                Word(alphanums).setResultsName('start_pos') +\
                                Word(alphanums).setResultsName('default_pos') +\
                                Word(alphanums).setResultsName('sex') +\
                                Word(nums).setResultsName('wealth') + Suppress(restOfLine) +\
                                Word(alphanums).setResultsName('form') +\
                                Word(alphanums).setResultsName('parts') +\
                                Word(alphanums).setResultsName('size') +\
                                Word(alphanums).setResultsName('material') + Suppress(restOfLine) +\
                                ZeroOrMore(
                                    Group(
                                        Suppress(Literal("F")) +\
                                        Word(alphas).setResultsName('word') +\
                                        Word(alphanums).setResultsName('flag')
                                    ).setResultsName('affects_f*')
                                )
                            )
                        ) + Suppress(Literal("#0"))

old_mobile_grammar  =   Suppress(Literal("#MOBOLD")) +\
                        ZeroOrMore(
                            Group(
                                vnum +\
                                tilde_string.setResultsName('name') + Suppress(restOfLine) +\
                                tilde_string.setResultsName('short_description') + Suppress(restOfLine) +\
                                tilde_string.setResultsName('long_description') + Suppress(restOfLine) +\
                                tilde_string.setResultsName('description') + Suppress(restOfLine) +\
                                Word(alphanums+"|").setResultsName('act') +\
                                Word(alphanums+"|").setResultsName('affected_by') +\
                                Word(nums+"-").setResultsName('alignment') +\
                                Suppress(Word(alphanums)) + Suppress(restOfLine) +\
                                Word(nums).setResultsName('level') +\
                                Suppress(Word(nums)) +\
                                Suppress(Word(nums)) +\
                                Suppress(Word(alphanums+"+")) +\
                                Suppress(Word(alphanums+"+")) + Suppress(restOfLine) +\
                                Word(nums).setResultsName('wealth') +\
                                Suppress(Word(nums)) + Suppress(restOfLine) +\
                                Word(nums).setResultsName('start_pos') +\
                                Word(nums).setResultsName('default_pos') +\
                                Word(nums).setResultsName('sex') + Suppress(restOfLine)
                            )
                        ) + Suppress(Literal("#0"))

reset_grammar       =   Suppress(Literal("#RESETS")) +\
                        ZeroOrMore(
                            Suppress(asterisk_comment) |
                            Group(Literal("G").setResultsName('command') + Suppress(Word("-" + nums)) + Word("-" + nums).setResultsName('arg1') + Word("-" + nums).setResultsName('arg2') + Suppress(restOfLine)) |
                            Group(Literal("R").setResultsName('command') + Suppress(Word("-" + nums)) + Word("-" + nums).setResultsName('arg1') + Word("-" + nums).setResultsName('arg2') + Suppress(restOfLine)) |
                            Group(Literal("O").setResultsName('command') + Suppress(Word("-" + nums)) + Word("-" + nums).setResultsName('arg1') + Word("-" + nums).setResultsName('arg2') + Word("-" + nums).setResultsName('arg3') + Suppress(restOfLine)) |
                            Group(Literal("E").setResultsName('command') + Suppress(Word("-" + nums)) + Word("-" + nums).setResultsName('arg1') + Word("-" + nums).setResultsName('arg2') + Word("-" + nums).setResultsName('arg3') + Suppress(restOfLine)) |
                            Group(Literal("D").setResultsName('command') + Suppress(Word("-" + nums)) + Word("-" + nums).setResultsName('arg1') + Word("-" + nums).setResultsName('arg2') + Word("-" + nums).setResultsName('arg3') + Suppress(restOfLine)) |
                            Group(Literal("P").setResultsName('command') + Suppress(Word("-" + nums)) + Word("-" + nums).setResultsName('arg1') + Word("-" + nums).setResultsName('arg2') + Word("-" + nums).setResultsName('arg3') + Word("-" + nums).setResultsName('arg4') + Suppress(restOfLine)) |
                            Group(Literal("M").setResultsName('command') + Suppress(Word("-" + nums)) + Word("-" + nums).setResultsName('arg1') + Word("-" + nums).setResultsName('arg2') + Word("-" + nums).setResultsName('arg3') + Word("-" + nums).setResultsName('arg4') + Suppress(restOfLine))
                        ) + Suppress(Literal("S"))

shop_grammar        =   Suppress(Literal("#SHOPS")) +\
                        ZeroOrMore(
                            Group(
                                Word(nums).setResultsName('keeper') +\
                                Word("-" + nums).setResultsName('buy_type_0') +\
                                Word("-" + nums).setResultsName('buy_type_1') +\
                                Word("-" + nums).setResultsName('buy_type_2') +\
                                Word("-" + nums).setResultsName('buy_type_3') +\
                                Word("-" + nums).setResultsName('buy_type_4') +\
                                Word("-" + nums).setResultsName('profit_buy') +\
                                Word("-" + nums).setResultsName('profit_sell') +\
                                Word("-" + nums).setResultsName('open_hour') +\
                                Word("-" + nums).setResultsName('close_hour') +\
                                Suppress(restOfLine)
                            )
                        ) + Suppress(Literal("0"))


olimit_grammar      =   Suppress(Literal("#OLIMITS")) +\
                        ZeroOrMore(
                            Group(
                                Suppress(Literal("O")) + Word(nums).setResultsName('vnum') + Word(nums).setResultsName('limit') + Suppress(restOfLine)
                            )
                        ) + Suppress(Literal("S"))

practicer_grammar   =   Suppress(Literal("#PRACTICERS")) +\
                        ZeroOrMore(
                            Suppress(asterisk_comment) |
                            Group(
                                Suppress(Literal("M")) + Word(nums).setResultsName('vnum') + Word(alphanums+"_").setResultsName('practicer') + Suppress(restOfLine)
                            )
                        ) + Suppress(Literal("S"))

special_grammar     =   Suppress(Literal("#SPECIALS")) +\
                        ZeroOrMore(
                            Suppress(asterisk_comment) |
                            Group(
                                Suppress(Literal("M")) + Word(nums).setResultsName('vnum') + Word(alphanums+"_").setResultsName('spec_fun') + Suppress(restOfLine)
                            )
                        ) + Suppress(Literal("S"))

omprog_grammar      =   Suppress(Literal("#OMPROGS")) +\
                        ZeroOrMore(
                            Suppress(asterisk_comment) |
                            Group(
                                one_of("M O").setResultsName('command') + Word(nums).setResultsName('vnum') + Word(alphanums+"_").setResultsName('progtype') + Word(alphanums+"_").setResultsName('progname') + Suppress(restOfLine)
                            )
                        ) + Suppress(Literal("S"))

help_grammar        =   Suppress(Literal("#HELPS")) +\
                        ZeroOrMore(
                            Suppress(Literal("0 $~")) |
                            Group(
                                Word("-"+nums).setResultsName('level') + tilde_string.setResultsName('keyword') + tilde_string.setResultsName('text')
                            )
                        )
                      
resetmessage_grammar=   Suppress(Literal("#RESETMESSAGE")) +\
                        tilde_string.setResultsName('area_reset_message')

areaflag_grammar    =   Suppress(Literal("#FLAG")) +\
                        Word(alphas).setResultsName('area_flag')


def parse_file(filemem):

    pattern         =   (Group(area_grammar).setResultsName("area") |\
                            Group(room_grammar).setResultsName("rooms") |\
                            Group(object_grammar).setResultsName("objects") |\
                            Group(old_object_grammar).setResultsName("old_objects") |\
                            Group(mobile_grammar).setResultsName("mobiles") |\
                            Group(old_mobile_grammar).setResultsName("old_mobiles") |\
                            Group(reset_grammar).setResultsName("resets") |\
                            Group(shop_grammar).setResultsName("shops") |\
                            Group(olimit_grammar).setResultsName("olimits") |\
                            Group(practicer_grammar).setResultsName("practicers") |\
                            Group(special_grammar).setResultsName("specials") |\
                            Group(omprog_grammar).setResultsName("omprogs") |\
                            Group(help_grammar).setResultsName("helps") |\
                            Group(resetmessage_grammar).setResultsName("area_reset_message") |\
                            Group(areaflag_grammar).setResultsName("area_flag")
                        )

    content         = ZeroOrMore(pattern)

    area_parser     = content + Suppress("#$")

    try:
        result      = area_parser.parse_string(filemem, parseAll=False)
        rr          = result.asDict()
        return rr
    except ParseException as pe:
       print(pe.markInputline())
       print(pe)
    return

def main():
    parser          = argparse.ArgumentParser(description='process anatolia 3.0 area file')
    parser.add_argument('area', help="Area file or list of areas", type=str)
    
    args            = parser.parse_args()
    
    with open(args.area+".are", "r") as f:
        data = parse_file(f.read())
    
    with open(args.area+".json", "w") as f:
        json.dump(data, f, indent=4)

    
if __name__ == "__main__":
    main()