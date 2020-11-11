from utils import get_tokens,remove_extra_white_spaces
from model_info import model_info
from normalizer import get_normalize_block_name
from simulink_preprocess import remove_graphic_component,keep_minimum_component_in_block
import os
class Restructure_mdl():
    '''
        This class provides utilities to restructure the Mdl Files
    '''

    def __init__(self,simulink_model_name,output_dir='slflat_output'):
        '''Instantiate a Restructure_mdl class variables .

                args:
                    simulink_model_name: Name of Simulink model . eg. xyz.mdl
                    output_dir: directory where the bfs restructured simulink model will be saved. This is used for training data
        '''

        self._file = simulink_model_name
        self._output_dir = output_dir
        self._structure_to_extract = { 'System','Block','Line'} # Hierarchy level in mdl elements.
        self._tmp_ext = '_TMP'# intermediate file that filters mdl file to only have System block { ... } . Output will be xyz_tmp.mdl
        self._bfs_ext = '_bfs' # output file saved in output directory... file name is xyz_bfs.mdl
        self._tmp_dir = 'slflat_tmp'
        self._valid_chk_dir = "slflat_V_CHK"
        if not os.path.exists(self._tmp_dir):
            os.mkdir(self._tmp_dir)
        if not os.path.exists(self._output_dir):
            os.mkdir(self._output_dir)
        if not os.path.exists(self._valid_chk_dir):
            os.mkdir(self._valid_chk_dir)

    def update_brace_count(self, line):
        '''
                keep track of brace count

                args:
                    line: line of the file
        '''
        assert(self._brace_count >= 0)
        self._brace_count += line.count('{')
        self._brace_count -= line.count('}')


    def extract_system_blk(self):
        '''
        extracts system block of the Simulink mdl file. Filter out everything else.
        The structure left in the output is Model { Name toy System { Name toy Block { .....} ... }}

        It also changes the name of the Simulink model to toy
        And It also updates the model_info object which keeps track of blocks and its connections. Necessary for bfs restructuring.
        returns:
            filtered list of line in the original file. Each element of the list corresponds to the line in the original file.
        '''
        self._brace_count = 0
        _processed_output = []
        stack = []
        stack_pop_brace_count = 0
        blk_info = ''
        line_info = ''
        mdl_info = model_info()

        with open(self._file, 'r') as file:
            for line in file:
                line = remove_extra_white_spaces(line)
                tokens = get_tokens(line)
                self.update_brace_count(line)
                #if self._brace_count==1 and stack[-1] != "Model":
                    #print("here")
                if "Model" == tokens[0]:
                    stack.append("Model")
                    _processed_output.append(line)
                    while get_tokens(line)[0] != "Name":
                        line = remove_extra_white_spaces(next(file))
                    _processed_output.append("Name toy")

                elif tokens[0] == "System" and stack[-1] == "Model":
                    stack_pop_brace_count += 1
                    stack.append(tokens[0])
                elif tokens[0] in self._structure_to_extract and stack[-1] != "Model":
                    stack_pop_brace_count += 1
                    stack.append(tokens[0])
                if stack[-1] in self._structure_to_extract:
                    if tokens[0] == "System":
                        _processed_output.append(line)
                        while get_tokens(line)[0] != "Name":
                            line = remove_extra_white_spaces(next(file))
                        _processed_output.append("Name toy")
                        while get_tokens(line)[0] != 'Block':
                            line = remove_extra_white_spaces(next(file))
                        stack.append('Block')
                        _processed_output.append(line)
                        #print(next_line)
                    else:
                        _processed_output.append(line)
                    if stack[-1] == "Block":

                        blk_info += line + "\n"
                    elif stack[-1] == "Line":
                        line_info += line + "\n"

                if stack_pop_brace_count == self._brace_count:
                    val = stack.pop()
                    if val == "Block":
                        #print(blk_info)
                        mdl_info.update_blk_info(blk_info)
                        blk_info = ''

                    elif val == "Line":
                        mdl_info.update_line_info(line_info)
                        line_info = ''
                    stack_pop_brace_count -= 1
                    if not stack:
                        try:
                            while True:
                                next_line = remove_extra_white_spaces(next(file))
                                _processed_output.append(next_line)
                        except StopIteration:
                            break
                    elif stack[-1] == "Model":
                        _processed_output.append(line)

        return _processed_output, mdl_info



    def restructure_single_mdl(self):
        '''
        Entry point for restructuring. Calls functions in a sequence.
        Each functions returned value is the input parameter to next function in the sequence.
        '''

        tmp_filename = self._file.split('/')[-1] .split('.')[0]+ self._tmp_ext + '.mdl'
        output_filename = self._file.split('/')[-1] .split('.')[0]+ self._bfs_ext + '.mdl'

        tmp_path  = os.path.join(self._tmp_dir,tmp_filename)
        output_path = os.path.join(self._output_dir,output_filename)
        output_filename = output_filename.replace('_bfs','_vbfs')
        print(output_filename)
        valid_chk_path  = os.path.join(self._valid_chk_dir,output_filename)

        tmp_output,model_info = self.extract_system_blk()
        self.save_to_file(tmp_path,  tmp_output)

        src, dest = model_info.get_src_dst()
        source_block = list(set(src).difference(set(dest)))
        output,org_norm_name_dict = self.bfs_ordering_new(source_block, model_info)
        #print("\n".join(output))

        output = remove_graphic_component("\n".join(output))
        self.save_to_file(output_path,output,org_norm_name_dict)
        #self.save_to_file(output_path, output)

        bfs_valid_output = self.bfs_ordering_validation(model_info)
        self.save_to_file(valid_chk_path, bfs_valid_output)

        #output = keep_minimum_component_in_block("\n".join(bfs_valid_output))
        #print("\n".join(output))
        #print(output)

    def save_to_file(self,  path, tmp_output,org_norm_name_dict = None):
        '''
        saves/write the list of line to a file.
        args:
            path : full path location of the file to which tmp_output is to be saved
            tmp_output: list of lines . Each element of the list corresponds to the line in the original file.
            org_norm_name_dict: dictionary with key : block name and value : normalized block name. Example clblk1 : a, clblk2: b and so on
        '''
        tmp = '\n'.join(tmp_output)
        if org_norm_name_dict is not None:
            for k,v in org_norm_name_dict.items():
                tmp = tmp.replace(k,v)

        with open(path,'w') as r:
            r.write(tmp)

    def bfs_ordering_validation(self,mdl_info):
        '''
        converts the BFS ordered Simulink file back to Simulink acceptable format: where Block {} defination comes first and then Line {} defination
        Caveat: Block with Block Type Outport have to be defined end of the all other block defination arranged in ascending order based on its port number
        while BLock Type Inport has to be defined beginning of the Block defination .
        Generated model may not have Port number.--> Port "2". In that case add port number
        args:
            path: full path of the Simulink model file.

        returns :
            list of lines where each element corresponds to the line in the processed file.
        '''
        blk_lst, line_lst = mdl_info.get_write_ready_blk_conn_list()
        _processed_output = ["Model {", "Name toy", "System {", "Name toy"]
        _processed_output += blk_lst
        _processed_output += line_lst
        _processed_output += ['}','}']
        return _processed_output

    def bfs_ordering_new(self, source_block, model_info):
        blk_names = [k for k in model_info.blk_info.keys()]
        orig_normalized_blk_names = {}
        name_counter = 1
        output = ["Model {", "Name toy", "System {", "Name toy"]
        unique_lines_added = set()

        while len(source_block) != 0 or len(blk_names)!=0:
            queue = []
            if len(source_block) != 0:
                queue.append(source_block[-1])
            elif len(blk_names)!=0:
                queue.append(blk_names[-1])
            while len(queue) != 0 :
                blk_visited = queue.pop(0)
                if blk_visited in blk_names:
                    if blk_visited not in orig_normalized_blk_names:
                        orig_normalized_blk_names[blk_visited] = get_normalize_block_name(name_counter)
                        name_counter += 1
                    block_code = model_info.blk_info[blk_visited]
                    output.append(block_code) # adding block code
                    blk_names.remove(blk_visited)
                    if blk_visited in model_info.graph:
                        for dest_edge in model_info.graph[blk_visited]:
                            (dest, edge) = dest_edge
                            if edge not in unique_lines_added:
                                output.append(edge)
                            unique_lines_added.add(edge)
                            for d in dest:
                                if d in blk_names:
                                    queue.append(d)
                    if blk_visited in model_info.graph_dest:
                        for src_edge in model_info.graph_dest[blk_visited]:
                            (src, edge) = src_edge
                            if edge not in unique_lines_added:
                                output.append(edge)
                            unique_lines_added.add(edge)
                            if src in blk_names:
                                queue.append(src)

                if blk_visited in source_block:
                    source_block.remove(blk_visited)
        output += ['}','}']
        return output,orig_normalized_blk_names





directory ='/home/sls6964xx/Desktop/SLNET_Flat_train_compile/'#'/home/sls6964xx/Desktop/Simulink_sample/'  #'/home/sls6964xx/Desktop/RandomMOdelGeneratorInMDLFormat/slsf/reportsneo/2020-09-02-14-27-55/success/'
count = 0
for files in os.listdir(directory):
    count +=1

    #print(count, " : ", files)
    try:
        processor = Restructure_mdl(os.path.join(directory,files))
        processor.restructure_single_mdl()
    except UnicodeDecodeError:
        continue
    except Exception as e:
        print(e)
        print("Error Processing : ", files)
        continue


    #print(os.path.join(directory,files))

# x = """slforge_100840958_166_bfs
# slforge_103070060_954_bfs
# slforge_109455323_290_bfs
# slforge_115263863_639_bfs
# slforge_116820486_221_bfs
# slforge_119186634_927_bfs
# slforge_133274971_348_bfs
# slforge_148707318_395_bfs
# slforge_149709169_219_bfs
# slforge_150345404_939_bfs
# slforge_163113637_196_bfs
# slforge_163854565_175_bfs
# slforge_181710094_759_bfs
# slforge_188187512_698_bfs
# slforge_189367667_469_bfs
# slforge_196111087_602_bfs
# slforge_20237467_545_bfs
# slforge_202430615_744_bfs
# slforge_202970885_712_bfs
# slforge_20481088_646_bfs
# slforge_207048500_218_bfs
# slforge_210634286_692_bfs
# slforge_212491956_153_bfs
# slforge_236447339_998_bfs
# slforge_239740698_723_bfs
# slforge_247780768_464_bfs
# slforge_25030590_338_bfs
# slforge_253621665_313_bfs
# slforge_259681077_575_bfs
# slforge_268651500_297_bfs
# slforge_269809720_749_bfs
# slforge_272727633_483_bfs
# slforge_27291099_748_bfs
# slforge_274629558_243_bfs
# slforge_281860843_280_bfs
# slforge_288255816_887_bfs
# slforge_305175039_251_bfs
# slforge_306276746_936_bfs
# slforge_306454103_402_bfs
# slforge_320213838_893_bfs
# slforge_320532988_724_bfs
# slforge_328622669_389_bfs
# slforge_354190334_811_bfs
# slforge_362651501_129_bfs
# slforge_363057801_463_bfs
# slforge_366782490_498_bfs
# slforge_368916070_75_bfs
# slforge_370965887_65_bfs
# slforge_375168036_195_bfs
# slforge_383621934_523_bfs
# slforge_385659974_145_bfs
# slforge_386064894_762_bfs
# slforge_414313477_261_bfs
# slforge_424015527_9_bfs
# slforge_44677512_731_bfs
# slforge_452162338_45_bfs
# slforge_45290452_365_bfs
# slforge_460001758_861_bfs
# slforge_460297509_29_bfs
# slforge_460717664_482_bfs
# slforge_463180451_414_bfs
# slforge_470271830_670_bfs
# slforge_488464452_891_bfs
# slforge_502656368_883_bfs
# slforge_503756812_121_bfs
# slforge_517493243_745_bfs
# slforge_517578157_995_bfs
# slforge_51784653_268_bfs
# slforge_518191258_766_bfs
# slforge_526578300_615_bfs
# slforge_531580834_679_bfs
# slforge_533772306_845_bfs
# slforge_544547412_512_bfs
# slforge_545863988_279_bfs
# slforge_554533673_570_bfs
# slforge_562144296_260_bfs
# slforge_576520496_795_bfs
# slforge_576695423_841_bfs
# slforge_581343008_213_bfs
# slforge_58619433_442_bfs
# slforge_589959545_690_bfs
# slforge_593669717_580_bfs
# slforge_603157444_717_bfs
# slforge_604864196_15_bfs
# slforge_629532953_696_bfs
# slforge_634359218_203_bfs
# slforge_63519104_453_bfs
# slforge_638420989_746_bfs
# slforge_64389875_235_bfs
# slforge_662331999_693_bfs
# slforge_685020956_528_bfs
# slforge_685874982_502_bfs
# slforge_689075942_894_bfs
# slforge_691789268_933_bfs
# slforge_698142696_332_bfs
# slforge_703836517_185_bfs
# slforge_726593191_504_bfs
# slforge_731631655_816_bfs
# slforge_739386461_787_bfs
# slforge_741391199_439_bfs
# slforge_747157772_39_bfs
# slforge_748022232_849_bfs
# slforge_752206838_518_bfs
# slforge_771357931_193_bfs
# slforge_773677176_427_bfs
# slforge_776864605_374_bfs
# slforge_782418194_837_bfs
# slforge_788013554_446_bfs
# slforge_795035487_20_bfs
# slforge_795178056_607_bfs
# slforge_795376787_738_bfs
# slforge_796142499_387_bfs
# slforge_796506880_323_bfs
# slforge_800377751_363_bfs
# slforge_800722030_943_bfs
# slforge_808528605_390_bfs
# slforge_816008054_325_bfs
# slforge_820199596_871_bfs
# slforge_823583653_826_bfs
# slforge_82728797_895_bfs
# slforge_838424996_721_bfs
# slforge_841811023_124_bfs
# slforge_845724132_94_bfs
# slforge_847146610_207_bfs
# slforge_855889869_122_bfs
# slforge_865938663_515_bfs
# slforge_867700888_451_bfs
# slforge_874257686_92_bfs
# slforge_879183608_282_bfs
# slforge_884675872_52_bfs
# slforge_890466769_84_bfs
# slforge_901896146_472_bfs
# slforge_903761901_741_bfs
# slforge_909796666_966_bfs
# slforge_915089740_278_bfs
# slforge_918899334_586_bfs
# slforge_919149785_173_bfs
# slforge_927035214_407_bfs
# slforge_942299490_660_bfs
# slforge_946325154_115_bfs
# slforge_947663464_852_bfs
# slforge_948753605_228_bfs
# slforge_95252572_830_bfs
# slforge_968765260_413_bfs
# slforge_975968524_772_bfs
# slforge_983568254_694_bfs
# slforge_993417501_353_bfs"""
# x = """slforge_105895491_798_bfs
# slforge_252468730_872_bfs
# slforge_344149598_657_bfs
# slforge_551054484_629_bfs
# slforge_566434247_50_bfs
# slforge_670967089_538_bfs
# slforge_733825341_495_bfs
# slforge_819207223_555_bfs
# slforge_888958867_636_bfs"""
# for k in x.split('\n'):
#     processor = Restructure_mdl('/home/sls6964xx/Documents/GPT2/gpt-2/preprocessor/output/'+k+'.mdl')#slforge_946325154_115_bfs.mdl')#('/home/sls6964xx/Desktop/RandomMOdelGeneratorInMDLFormat/slsf/reportsneo/2020-09-02-14-27-55/success/slforge_598683771_989.mdl')
#     processor.restructure_single_mdl()
# processor = Restructure_mdl('/home/sls6964xx/Documents/GPT2/gpt-2/src/sample.mdl')#slforge_946325154_115_bfs.mdl')#('/home/sls6964xx/Desktop/RandomMOdelGeneratorInMDLFormat/slsf/reportsneo/2020-09-02-14-27-55/success/slforge_598683771_989.mdl')
# processor.restructure_single_mdl()

# processor = Restructure_mdl('/home/sls6964xx/Desktop/RandomMOdelGeneratorInMDLFormat/slsf/reportsneo/2020-09-02-14-27-55/success/slforge_598683771_989.mdl')
# processor.restructure_single_mdl()
