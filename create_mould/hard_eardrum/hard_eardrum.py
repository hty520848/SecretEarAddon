from ..normal_projection import normal_projection_to_darw_bottom_ring
from ..bottom_ring import soft_eardrum_bottom_cut
from ..thickness import init_thickness


def apply_hard_eardrum_template():
    origin_highest_vert = (-10.5040, 2.6564, 11.9506)
    border_vert_co_and_normal = [
        ((-4.81834602355957, 1.1757267713546753, 1.5148240327835083),
         (0.7272932529449463, 0.3362278640270233, 0.5983271598815918)), (
            (-4.815596580505371, 0.8645016551017761, 1.663185477256775),
            (0.7319542765617371, 0.27526453137397766, 0.6232754588127136)), (
            (-4.8254241943359375, 0.5429428219795227, 1.8049442768096924),
            (0.7295067310333252, 0.24646009504795074, 0.6380261778831482)), (
            (-4.840545177459717, 0.2127116322517395, 1.940894603729248),
            (0.7279173731803894, 0.23846492171287537, 0.6428613662719727)), (
            (-4.8519134521484375, -0.1232953891158104, 2.075254201889038),
            (0.7270979881286621, 0.2243415266275406, 0.6488445401191711)), (
            (-4.924487590789795, -1.1714022159576416, 2.4225759506225586),
            (0.7135840058326721, 0.09768951684236526, 0.6937252283096313)), (
            (-4.888246536254883, -0.8134791851043701, 2.323955774307251),
            (0.7166069149971008, 0.14310677349567413, 0.6826381683349609)), (
            (-4.864531993865967, -0.46400973200798035, 2.2084829807281494),
            (0.7236316800117493, 0.18931888043880463, 0.6637135148048401)), (
            (-4.969106197357178, -1.5373759269714355, 2.505880832672119),
            (0.7129580974578857, 0.055270496755838394, 0.6990249156951904)), (
            (-5.019659519195557, -1.911088466644287, 2.5767641067504883),
            (0.708958625793457, 0.009882676415145397, 0.7051808834075928)), (
            (-5.0796942710876465, -2.2927262783050537, 2.630708694458008),
            (0.7021994590759277, -0.028346378356218338, 0.7114157676696777)), (
            (-5.289381980895996, -3.4985764026641846, 2.7193381786346436),
            (0.6455903649330139, -0.10157027840614319, 0.7568992376327515)), (
            (-5.214091777801514, -3.085059881210327, 2.7017571926116943),
            (0.6654545664787292, -0.08204462379217148, 0.741915762424469)), (
            (-5.144651889801025, -2.683812141418457, 2.671999454498291),
            (0.688339114189148, -0.05500219762325287, 0.7233008146286011)), (
            (-5.450777053833008, 2.7887730598449707, 0.06980912387371063),
            (0.4710165560245514, 0.8672558665275574, 0.16127829253673553)), (
            (-5.291178226470947, 2.641733407974243, 0.3162119388580322),
            (0.5280616879463196, 0.8191512227058411, 0.22392414510250092)), (
            (-5.152560234069824, 2.4632818698883057, 0.5512966513633728),
            (0.5861966609954834, 0.7538842558860779, 0.29670166969299316)), (
            (-5.038965225219727, 2.2495620250701904, 0.7734338641166687),
            (0.6325696706771851, 0.6767933964729309, 0.3765716850757599)), (
            (-4.948114395141602, 2.0118696689605713, 0.9800415635108948),
            (0.6652994751930237, 0.5889297127723694, 0.4588446617126465)), (
            (-4.844980239868164, 1.4699770212173462, 1.3511847257614136),
            (0.7116926312446594, 0.4111262857913971, 0.5696215629577637)), (
            (-4.884517669677734, 1.7499505281448364, 1.1710894107818604),
            (0.6898139119148254, 0.49505358934402466, 0.5282790064811707)), (
            (-5.551578998565674, -4.811647891998291, 2.710542678833008),
            (0.5685786604881287, -0.19762109220027924, 0.7985388040542603)), (
            (-5.452030658721924, -4.36153507232666, 2.7278521060943604),
            (0.6052792072296143, -0.14177004992961884, 0.7832868099212646)), (
            (-5.368056774139404, -3.923370122909546, 2.7273809909820557),
            (0.6288585662841797, -0.11385029554367065, 0.7691391706466675)), (
            (-9.643643379211426, -11.221138000488281, -1.2382394075393677),
            (-0.8210748434066772, -0.5454843044281006, -0.16817563772201538)), (
            (-9.592426300048828, -11.147829055786133, -1.5441046953201294),
            (-0.7908353805541992, -0.5144450068473816, -0.33155032992362976)), (
            (-9.501543998718262, -11.039148330688477, -1.8429591655731201),
            (-0.7597813010215759, -0.45884326100349426, -0.46064677834510803)), (
            (-9.368955612182617, -10.914258003234863, -2.1330621242523193),
            (-0.7304683327674866, -0.3898981809616089, -0.5607097148895264)), (
            (-5.9651007652282715, -6.194329738616943, 2.5592803955078125),
            (0.42312726378440857, -0.260259211063385, 0.8678872585296631)), (
            (-5.814375400543213, -5.728737831115723, 2.6121959686279297),
            (0.4759048521518707, -0.24592719972133636, 0.8444135785102844)), (
            (-5.676632404327393, -5.26694393157959, 2.6644845008850098),
            (0.5236678123474121, -0.2375202775001526, 0.8181419372558594)), (
            (-6.136291027069092, -6.659034729003906, 2.493377447128296),
            (0.37202197313308716, -0.2811058759689331, 0.8846350312232971)), (
            (-6.324950695037842, -7.121334552764893, 2.418924570083618),
            (0.3229649066925049, -0.2997919023036957, 0.8976739645004272)), (
            (-6.531499862670898, -7.57425594329834, 2.332918167114258),
            (0.26283594965934753, -0.325397789478302, 0.908313512802124)), (
            (-7.252013683319092, -8.84841251373291, 1.9721261262893677),
            (0.030232874676585197, -0.3350331485271454, 0.9417211413383484)), (
            (-6.997767925262451, -8.441020011901855, 2.1006417274475098),
            (0.10417209565639496, -0.3502640426158905, 0.9308400750160217)), (
            (-6.757197856903076, -8.014206886291504, 2.2258994579315186),
            (0.18582871556282043, -0.3485327363014221, 0.9186906814575195)), (
            (-7.512246131896973, -9.22889518737793, 1.841762661933899),
            (-0.040329333394765854, -0.32578620314598083, 0.944582998752594)), (
            (-7.771860122680664, -9.585030555725098, 1.6992783546447754),
            (-0.12242985516786575, -0.3362691402435303, 0.9337740540504456)), (
            (-8.033587455749512, -9.898443222045898, 1.5288324356079102),
            (-0.21823789179325104, -0.35358133912086487, 0.9095892310142517)), (
            (-8.779386520385742, -10.62386417388916, 0.8728341460227966),
            (-0.49893754720687866, -0.40784257650375366, 0.7646737098693848)), (
            (-8.54136848449707, -10.412405967712402, 1.1143957376480103),
            (-0.4194379448890686, -0.39183130860328674, 0.8188651204109192)), (
            (-8.291070938110352, -10.172082901000977, 1.3375781774520874),
            (-0.32221555709838867, -0.37311550974845886, 0.8700355887413025)), (
            (-9.512489318847656, -11.167228698730469, -0.28159385919570923),
            (-0.7628558278083801, -0.518887460231781, 0.38575485348701477)), (
            (-9.604914665222168, -11.223713874816895, -0.6046149134635925),
            (-0.8087788224220276, -0.5377049446105957, 0.23822319507598877)), (
            (-9.655610084533691, -11.248445510864258, -0.9231840372085571),
            (-0.832838237285614, -0.5520491600036621, 0.0402747318148613)), (
            (-9.378199577331543, -11.079549789428711, 0.03544919192790985),
            (-0.7003133893013, -0.4938947558403015, 0.5153923630714417)), (
            (-9.205605506896973, -10.958497047424316, 0.3353654444217682),
            (-0.6289557218551636, -0.45851826667785645, 0.627834141254425)), (
            (-9.000862121582031, -10.804564476013184, 0.6115149855613708),
            (-0.5636173486709595, -0.4272848069667816, 0.7069393396377563)), (
            (-9.017584800720215, -10.666501998901367, -2.664405584335327),
            (-0.7169671058654785, -0.2601000666618347, -0.6467658281326294)), (
            (-9.198643684387207, -10.779619216918945, -2.4055159091949463),
            (-0.7164823412895203, -0.3235905170440674, -0.6180148124694824)), (
            (-8.813863754272461, -10.57830810546875, -2.9126458168029785),
            (-0.7172549366950989, -0.1966293752193451, -0.6684924960136414)), (
            (-7.361071586608887, -6.210186004638672, -5.219229221343994),
            (-0.5538044571876526, -0.26454028487205505, -0.7895056009292603)), (
            (-7.501965522766113, -5.810930252075195, -5.2588019371032715),
            (-0.541024386882782, -0.2723258435726166, -0.795695424079895)), (
            (-7.652006149291992, -5.415909290313721, -5.293013572692871),
            (-0.5326900482177734, -0.2700999975204468, -0.802051842212677)), (
            (-7.807971477508545, -5.017689228057861, -5.323968410491943),
            (-0.5282593369483948, -0.25900930166244507, -0.8086137771606445)), (
            (-7.962447643280029, -4.6208720207214355, -5.3439717292785645),
            (-0.5274047255516052, -0.23696276545524597, -0.8159000277519226)), (
            (-8.392023086547852, -3.4300484657287598, -5.339328765869141),
            (-0.5343877077102661, -0.1243273913860321, -0.8360456824302673)), (
            (-8.258009910583496, -3.825972318649292, -5.353079795837402),
            (-0.5313422083854675, -0.16640828549861908, -0.8306524753570557)), (
            (-8.114428520202637, -4.223365783691406, -5.355592727661133),
            (-0.5286997556686401, -0.2043076455593109, -0.8238536715507507)), (
            (-5.983525276184082, 3.104417324066162, -0.7109248042106628),
            (0.368741899728775, 0.9294978976249695, 0.007937480695545673)), (
            (-5.800852298736572, 3.017759084701538, -0.44572409987449646),
            (0.40023818612098694, 0.9139727354049683, 0.06680690497159958)), (
            (-5.623973846435547, 2.9114837646484375, -0.1855292022228241),
            (0.42961522936820984, 0.8960053324699402, 0.1122734397649765)), (
            (-8.704054832458496, -2.248490810394287, -5.22361421585083),
            (-0.5388423800468445, 0.002401899080723524, -0.8424032926559448)), (
            (-8.615948677062988, -2.6415579319000244, -5.272800445556641),
            (-0.5385972857475281, -0.042050786316394806, -0.8415133953094482)), (
            (-8.510735511779785, -3.034374713897705, -5.310336112976074),
            (-0.5366756319999695, -0.08239539712667465, -0.8397560119628906)), (
            (-8.775628089904785, -1.8569573163986206, -5.165129661560059),
            (-0.5356601476669312, 0.04703529179096222, -0.843122661113739)), (
            (-8.83004093170166, -1.4658199548721313, -5.09797477722168),
            (-0.529760479927063, 0.09288358688354492, -0.8430458903312683)), (
            (-8.864624977111816, -1.074968695640564, -5.02143669128418),
            (-0.5201097726821899, 0.14398984611034393, -0.8418745398521423)), (
            (-8.851223945617676, 0.08745326846837997, -4.730405807495117),
            (-0.47482484579086304, 0.2828075885772705, -0.8334034085273743)), (
            (-8.874214172363281, -0.2965981960296631, -4.838684558868408),
            (-0.4904588758945465, 0.24009408056735992, -0.8377379775047302)), (
            (-8.878171920776367, -0.6850125193595886, -4.934300422668457),
            (-0.506513774394989, 0.19305960834026337, -0.840340256690979)), (
            (-8.81279182434082, 0.46761566400527954, -4.613390922546387),
            (-0.4617832601070404, 0.3219873011112213, -0.8264867663383484)), (
            (-8.759034156799316, 0.841400682926178, -4.487545013427734),
            (-0.4512496590614319, 0.3619519770145416, -0.8156987428665161)), (
            (-8.688373565673828, 1.2075425386428833, -4.352637767791748),
            (-0.4395352900028229, 0.4071827530860901, -0.8006317019462585)), (
            (-8.335921287536621, 2.1762568950653076, -3.8395512104034424),
            (-0.28322306275367737, 0.6758807897567749, -0.6804189682006836)), (
            (-8.482318878173828, 1.8866208791732788, -4.039639472961426),
            (-0.3458911180496216, 0.5875990390777588, -0.7314962148666382)), (
            (-8.600456237792969, 1.560542345046997, -4.210196018218994),
            (-0.40695178508758545, 0.4845636785030365, -0.7743309140205383)), (
            (-8.169185638427734, 2.432870388031006, -3.622918128967285),
            (-0.22572952508926392, 0.7471204400062561, -0.6251857876777649)), (
            (-7.988043308258057, 2.655459403991699, -3.391937017440796),
            (-0.16334432363510132, 0.8073816895484924, -0.5669687390327454)), (
            (-7.794227600097656, 2.8416879177093506, -3.146817207336426),
            (-0.0960940346121788, 0.8547372817993164, -0.5100883841514587)), (
            (-7.1759724617004395, 3.188124179840088, -2.363201141357422),
            (0.14056482911109924, 0.936789870262146, -0.3204156458377838)), (
            (-7.383982181549072, 3.1136932373046875, -2.6331918239593506),
            (0.06345469504594803, 0.9205977320671082, -0.38532233238220215)), (
            (-7.591915130615234, 2.9971189498901367, -2.8945984840393066),
            (-0.020448407158255577, 0.8919512629508972, -0.4516688287258148)), (
            (-6.968369007110596, 3.233053207397461, -2.08803129196167),
            (0.20276468992233276, 0.9439417123794556, -0.2605002522468567)), (
            (-6.763601303100586, 3.2490296363830566, -1.8098608255386353),
            (0.25041452050209045, 0.9467874765396118, -0.20220351219177246)), (
            (-6.561617851257324, 3.242220163345337, -1.53142249584198),
            (0.2825718820095062, 0.9466691017150879, -0.15482495725154877)), (
            (-6.170737266540527, 3.172534465789795, -0.9812360405921936),
            (0.3381095826625824, 0.939632773399353, -0.05265209078788757)), (
            (-6.363662242889404, 3.2176780700683594, -1.2550536394119263),
            (0.3101139962673187, 0.9446213841438293, -0.10732997208833694)), (
            (-8.605518341064453, -10.527613639831543, -3.1473281383514404),
            (-0.7274553179740906, -0.1416345238685608, -0.6713780164718628)), (
            (-8.396940231323242, -10.513721466064453, -3.3849844932556152),
            (-0.7456120848655701, -0.09725384414196014, -0.6592452526092529)), (
            (-7.652744770050049, -10.689099311828613, -4.3794355392456055),
            (-0.8502781987190247, 0.016449667513370514, -0.5260763764381409)), (
            (-7.490937232971191, -10.750536918640137, -4.6571245193481445),
            (-0.8760229349136353, 0.038284096866846085, -0.48074743151664734)), (
            (-7.825462341308594, -10.633231163024902, -4.115240573883057),
            (-0.8268214464187622, -0.004370536655187607, -0.5624474287033081)), (
            (-8.00579833984375, -10.581867218017578, -3.8602473735809326),
            (-0.8032576441764832, -0.02946670912206173, -0.5949023962020874)), (
            (-8.196702003479004, -10.53685474395752, -3.6186625957489014),
            (-0.7732548117637634, -0.06092022731900215, -0.631162166595459)), (
            (-7.185281276702881, -9.782986640930176, -5.041965484619141),
            (-0.8472612500190735, 0.10885260254144669, -0.5199033617973328)), (
            (-7.2711310386657715, -10.298072814941406, -5.002803802490234),
            (-0.8765673637390137, 0.09693276882171631, -0.4714166224002838)), (
            (-7.347939491271973, -10.817234992980957, -4.948492527008057),
            (-0.9009276032447815, 0.06616704165935516, -0.42889559268951416)), (
            (-7.066139221191406, -7.456679821014404, -5.109371662139893),
            (-0.6442299485206604, -0.1288101226091385, -0.7539070248603821)), (
            (-7.137125015258789, -7.031135082244873, -5.1389970779418945),
            (-0.6080389022827148, -0.1849479228258133, -0.7720640897750854)), (
            (-7.23530387878418, -6.617312908172607, -5.175982475280762),
            (-0.5761701464653015, -0.23501881957054138, -0.7828117609024048)), (
            (-7.007826805114746, -8.33644962310791, -5.0786919593811035),
            (-0.7265421748161316, 0.005115486215800047, -0.6871029734611511)), (
            (-7.037045955657959, -8.80008602142334, -5.073358535766602),
            (-0.7694128751754761, 0.07117023319005966, -0.6347745060920715)), (
            (-7.1053786277771, -9.282160758972168, -5.066983699798584),
            (-0.8111454248428345, 0.10416878014802933, -0.575492799282074)), (
            (-7.019528388977051, -7.888681411743164, -5.090011119842529),
            (-0.6839302182197571, -0.0663234293460846, -0.7265264987945557))
    ]

    normal_projection_to_darw_bottom_ring(origin_highest_vert, border_vert_co_and_normal)
    soft_eardrum_bottom_cut()

    # todo 封底
