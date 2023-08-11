{
	"patcher" : 	{
		"fileversion" : 1,
		"appversion" : 		{
			"major" : 8,
			"minor" : 5,
			"revision" : 5,
			"architecture" : "x64",
			"modernui" : 1
		}
,
		"classnamespace" : "box",
		"rect" : [ 155.0, 87.0, 754.0, 624.0 ],
		"bglocked" : 0,
		"openinpresentation" : 0,
		"default_fontsize" : 11.595186999999999,
		"default_fontface" : 0,
		"default_fontname" : "Lato",
		"gridonopen" : 1,
		"gridsize" : [ 15.0, 15.0 ],
		"gridsnaponopen" : 1,
		"objectsnaponopen" : 1,
		"statusbarvisible" : 2,
		"toolbarvisible" : 1,
		"lefttoolbarpinned" : 0,
		"toptoolbarpinned" : 0,
		"righttoolbarpinned" : 0,
		"bottomtoolbarpinned" : 0,
		"toolbars_unpinned_last_save" : 0,
		"tallnewobj" : 0,
		"boxanimatetime" : 200,
		"enablehscroll" : 1,
		"enablevscroll" : 1,
		"devicewidth" : 0.0,
		"description" : "",
		"digest" : "",
		"tags" : "",
		"style" : "",
		"subpatcher_template" : "",
		"assistshowspatchername" : 0,
		"boxes" : [ 			{
				"box" : 				{
					"bubble" : 1,
					"fontname" : "Lato",
					"fontsize" : 13.0,
					"id" : "obj-70",
					"maxclass" : "comment",
					"numinlets" : 1,
					"numoutlets" : 0,
					"patching_rect" : [ 232.0, 534.0, 94.0, 26.0 ],
					"text" : "Start Audio"
				}

			}
, 			{
				"box" : 				{
					"fontface" : 0,
					"fontname" : "Lato",
					"fontsize" : 12.0,
					"id" : "obj-34",
					"maxclass" : "tab",
					"numinlets" : 1,
					"numoutlets" : 3,
					"outlettype" : [ "int", "", "" ],
					"parameter_enable" : 0,
					"patching_rect" : [ 370.0, 210.0, 59.0, 62.0 ],
					"tabs" : [ "demo", "loop", "off" ]
				}

			}
, 			{
				"box" : 				{
					"fontface" : 1,
					"fontname" : "Lato",
					"fontsize" : 11.0,
					"id" : "obj-23",
					"maxclass" : "comment",
					"numinlets" : 1,
					"numoutlets" : 0,
					"patching_rect" : [ 661.0, 8.0, 84.0, 20.0 ],
					"text" : "<, j.goode, jkc"
				}

			}
, 			{
				"box" : 				{
					"fontsize" : 12.754706000000001,
					"id" : "obj-61",
					"maxclass" : "preset",
					"numinlets" : 1,
					"numoutlets" : 5,
					"outlettype" : [ "preset", "int", "preset", "int", "" ],
					"patching_rect" : [ 215.0, 285.0, 53.0, 30.0 ],
					"preset_data" : [ 						{
							"number" : 1,
							"data" : [ 4, "obj-43", "function", "clear", 7, "obj-43", "function", "add", 0.0, 0.0, 0, 7, "obj-43", "function", "add", 1286.054442999999992, 1286.054442999999992, 0, 5, "obj-43", "function", "domain", 1286.054442999999992, 6, "obj-43", "function", "range", 0.0, 1286.054442999999992, 5, "obj-43", "function", "mode", 0 ]
						}
, 						{
							"number" : 2,
							"data" : [ 4, "obj-43", "function", "clear", 7, "obj-43", "function", "add", 0.0, 0.0, 0, 7, "obj-43", "function", "add", 241.975403, 869.705871999999999, 0, 7, "obj-43", "function", "add", 569.09027100000003, 453.35732999999999, 0, 7, "obj-43", "function", "add", 1286.054442999999992, 1286.054442999999992, 0, 5, "obj-43", "function", "domain", 1286.054442999999992, 6, "obj-43", "function", "range", 0.0, 1286.054442999999992, 5, "obj-43", "function", "mode", 0 ]
						}
, 						{
							"number" : 3,
							"data" : [ 4, "obj-43", "function", "clear", 7, "obj-43", "function", "add", 0.0, 0.0, 0, 7, "obj-43", "function", "add", 71.696419000000006, 888.210266000000047, 0, 7, "obj-43", "function", "add", 851.394897000000014, 212.800368999999989, 0, 7, "obj-43", "function", "add", 1286.054442999999992, 1286.054442999999992, 0, 5, "obj-43", "function", "domain", 1286.054442999999992, 6, "obj-43", "function", "range", 0.0, 1286.054442999999992, 5, "obj-43", "function", "mode", 0 ]
						}
, 						{
							"number" : 4,
							"data" : [ 4, "obj-43", "function", "clear", 7, "obj-43", "function", "add", 0.0, 0.0, 0, 7, "obj-43", "function", "add", 174.760009999999994, 194.295989999999989, 0, 7, "obj-43", "function", "add", 255.418472000000008, 573.63580300000001, 0, 7, "obj-43", "function", "add", 703.521057000000042, 462.609496999999976, 0, 7, "obj-43", "function", "add", 1070.96521000000007, 120.278473000000005, 0, 7, "obj-43", "function", "add", 1286.054442999999992, 1286.054442999999992, 0, 5, "obj-43", "function", "domain", 1286.054442999999992, 6, "obj-43", "function", "range", 0.0, 1286.054442999999992, 5, "obj-43", "function", "mode", 0 ]
						}
, 						{
							"number" : 5,
							"data" : [ 4, "obj-43", "function", "clear", 7, "obj-43", "function", "add", 0.0, 0.0, 0, 7, "obj-43", "function", "add", 134.430770999999993, 1286.054442999999992, 0, 7, "obj-43", "function", "add", 165.797957999999994, 194.295989999999989, 0, 7, "obj-43", "function", "add", 389.849243000000001, 194.295989999999989, 0, 7, "obj-43", "function", "add", 407.773346000000004, 1175.028197999999975, 0, 7, "obj-43", "function", "add", 622.862610000000018, 1193.532592999999906, 0, 7, "obj-43", "function", "add", 654.229796999999962, 157.287230999999991, 0, 7, "obj-43", "function", "add", 864.838013000000046, 157.287230999999991, 0, 7, "obj-43", "function", "add", 954.458495999999968, 1221.289062000000058, 0, 7, "obj-43", "function", "add", 1062.003173999999944, 1230.541259999999966, 0, 7, "obj-43", "function", "add", 1062.003173999999944, 148.035048999999987, 0, 7, "obj-43", "function", "add", 1286.054442999999992, 148.035048999999987, 0, 5, "obj-43", "function", "domain", 1286.054442999999992, 6, "obj-43", "function", "range", 0.0, 1286.054442999999992, 5, "obj-43", "function", "mode", 0 ]
						}
, 						{
							"number" : 6,
							"data" : [ 4, "obj-43", "function", "clear", 7, "obj-43", "function", "add", 0.0, 0.0, 0, 7, "obj-43", "function", "add", 286.785675000000026, 1286.054442999999992, 0, 7, "obj-43", "function", "add", 286.785675000000026, 259.061339999999973, 0, 7, "obj-43", "function", "add", 389.849243000000001, 194.295989999999989, 0, 7, "obj-43", "function", "add", 488.431824000000006, 1184.28039600000011, 0, 7, "obj-43", "function", "add", 622.862610000000018, 1193.532592999999906, 0, 7, "obj-43", "function", "add", 766.255432000000042, 166.539429000000013, 0, 7, "obj-43", "function", "add", 864.838013000000046, 157.287230999999991, 0, 7, "obj-43", "function", "add", 954.458495999999968, 1221.289062000000058, 0, 7, "obj-43", "function", "add", 1026.154907000000094, 1249.045654000000013, 0, 7, "obj-43", "function", "add", 1062.003173999999944, 148.035048999999987, 0, 7, "obj-43", "function", "add", 1286.054442999999992, 148.035048999999987, 0, 5, "obj-43", "function", "domain", 1286.054442999999992, 6, "obj-43", "function", "range", 0.0, 1286.054442999999992, 5, "obj-43", "function", "mode", 0 ]
						}
, 						{
							"number" : 7,
							"data" : [ 4, "obj-43", "function", "clear", 7, "obj-43", "function", "add", 0.0, 0.0, 0, 7, "obj-43", "function", "add", 80.658469999999994, 0.0, 0, 7, "obj-43", "function", "add", 85.139495999999994, 462.609496999999976, 0, 7, "obj-43", "function", "add", 129.949752999999987, 453.35732999999999, 0, 7, "obj-43", "function", "add", 134.430770999999993, 1286.054442999999992, 0, 7, "obj-43", "function", "add", 179.241042999999991, 1276.802245999999968, 0, 7, "obj-43", "function", "add", 192.684112999999996, 249.809143000000006, 0, 7, "obj-43", "function", "add", 259.899505999999974, 277.565703999999982, 0, 7, "obj-43", "function", "add", 268.861541999999986, 851.201476999999954, 0, 7, "obj-43", "function", "add", 403.292327999999998, 841.949341000000004, 0, 7, "obj-43", "function", "add", 407.773346000000004, 1175.028197999999975, 0, 7, "obj-43", "function", "add", 474.98873900000001, 1110.262817000000041, 0, 7, "obj-43", "function", "add", 474.98873900000001, 138.782851999999991, 0, 7, "obj-43", "function", "add", 537.723082999999974, 138.782851999999991, 0, 7, "obj-43", "function", "add", 537.723082999999974, 1221.289062000000058, 0, 7, "obj-43", "function", "add", 604.938477000000034, 1212.036865000000034, 0, 7, "obj-43", "function", "add", 613.900574000000006, 111.026283000000006, 0, 7, "obj-43", "function", "add", 882.762084999999956, 129.530669999999986, 0, 7, "obj-43", "function", "add", 954.458495999999968, 1221.289062000000058, 0, 7, "obj-43", "function", "add", 1062.003173999999944, 1230.541259999999966, 0, 7, "obj-43", "function", "add", 1062.003173999999944, 148.035048999999987, 0, 7, "obj-43", "function", "add", 1178.5097659999999, 138.782851999999991, 0, 7, "obj-43", "function", "add", 1209.876952999999958, 1286.054442999999992, 0, 7, "obj-43", "function", "add", 1245.725220000000036, 1258.297851999999921, 0, 7, "obj-43", "function", "add", 1245.725220000000036, 138.782851999999991, 0, 7, "obj-43", "function", "add", 1286.054442999999992, 148.035048999999987, 0, 7, "obj-43", "function", "add", 1286.054442999999992, 148.035048999999987, 0, 5, "obj-43", "function", "domain", 1286.054442999999992, 6, "obj-43", "function", "range", 0.0, 1286.054442999999992, 5, "obj-43", "function", "mode", 0 ]
						}
, 						{
							"number" : 8,
							"data" : [ 4, "obj-43", "function", "clear", 7, "obj-43", "function", "add", 0.0, 0.0, 0, 7, "obj-43", "function", "add", 80.658469999999994, 0.0, 0, 7, "obj-43", "function", "add", 85.139495999999994, 462.609496999999976, 0, 7, "obj-43", "function", "add", 129.949752999999987, 453.35732999999999, 0, 7, "obj-43", "function", "add", 134.430770999999993, 1286.054442999999992, 0, 7, "obj-43", "function", "add", 179.241042999999991, 1276.802245999999968, 0, 7, "obj-43", "function", "add", 192.684112999999996, 249.809143000000006, 0, 7, "obj-43", "function", "add", 259.899505999999974, 277.565703999999982, 0, 7, "obj-43", "function", "add", 268.861541999999986, 851.201476999999954, 0, 7, "obj-43", "function", "add", 403.292327999999998, 841.949341000000004, 0, 7, "obj-43", "function", "add", 407.773346000000004, 1175.028197999999975, 0, 7, "obj-43", "function", "add", 569.09027100000003, 1165.776000999999951, 0, 7, "obj-43", "function", "add", 569.09027100000003, 157.287230999999991, 0, 7, "obj-43", "function", "add", 640.786682000000042, 148.035048999999987, 0, 7, "obj-43", "function", "add", 658.710815000000025, 1267.550048999999944, 0, 7, "obj-43", "function", "add", 712.483093000000054, 1239.793456999999989, 0, 7, "obj-43", "function", "add", 712.483093000000054, 129.530669999999986, 0, 7, "obj-43", "function", "add", 761.774413999999979, 157.287230999999991, 0, 7, "obj-43", "function", "add", 761.774413999999979, 1249.045654000000013, 0, 7, "obj-43", "function", "add", 797.622619999999984, 1276.802245999999968, 0, 7, "obj-43", "function", "add", 802.103638000000046, 166.539429000000013, 0, 7, "obj-43", "function", "add", 824.508788999999979, 148.035048999999987, 0, 7, "obj-43", "function", "add", 837.951843000000054, 1184.28039600000011, 0, 7, "obj-43", "function", "add", 864.838013000000046, 1184.28039600000011, 0, 7, "obj-43", "function", "add", 864.838013000000046, 157.287230999999991, 0, 7, "obj-43", "function", "add", 954.458495999999968, 1221.289062000000058, 0, 7, "obj-43", "function", "add", 1062.003173999999944, 1230.541259999999966, 0, 7, "obj-43", "function", "add", 1062.003173999999944, 148.035048999999987, 0, 7, "obj-43", "function", "add", 1178.5097659999999, 138.782851999999991, 0, 7, "obj-43", "function", "add", 1209.876952999999958, 1286.054442999999992, 0, 7, "obj-43", "function", "add", 1245.725220000000036, 1258.297851999999921, 0, 7, "obj-43", "function", "add", 1245.725220000000036, 138.782851999999991, 0, 7, "obj-43", "function", "add", 1286.054442999999992, 148.035048999999987, 0, 7, "obj-43", "function", "add", 1286.054442999999992, 148.035048999999987, 0, 5, "obj-43", "function", "domain", 1286.054442999999992, 6, "obj-43", "function", "range", 0.0, 1286.054442999999992, 5, "obj-43", "function", "mode", 0 ]
						}
 ]
				}

			}
, 			{
				"box" : 				{
					"fontface" : 1,
					"fontname" : "Lato",
					"fontsize" : 12.0,
					"id" : "obj-60",
					"maxclass" : "comment",
					"numinlets" : 1,
					"numoutlets" : 0,
					"patching_rect" : [ 478.0, 567.0, 62.0, 21.0 ],
					"text" : "real time"
				}

			}
, 			{
				"box" : 				{
					"fontface" : 1,
					"fontname" : "Lato",
					"fontsize" : 12.0,
					"id" : "obj-59",
					"linecount" : 2,
					"maxclass" : "comment",
					"numinlets" : 1,
					"numoutlets" : 0,
					"patching_rect" : [ 649.0, 399.0, 50.0, 35.0 ],
					"text" : "end of sample"
				}

			}
, 			{
				"box" : 				{
					"fontface" : 1,
					"fontname" : "Lato",
					"fontsize" : 12.0,
					"id" : "obj-58",
					"linecount" : 2,
					"maxclass" : "comment",
					"numinlets" : 1,
					"numoutlets" : 0,
					"patching_rect" : [ 649.0, 530.0, 69.0, 35.0 ],
					"text" : "beginning of sample"
				}

			}
, 			{
				"box" : 				{
					"fontface" : 1,
					"fontname" : "Lato",
					"fontsize" : 12.0,
					"id" : "obj-57",
					"maxclass" : "comment",
					"numinlets" : 1,
					"numoutlets" : 0,
					"patching_rect" : [ 712.0, 580.0, 26.0, 21.0 ],
					"text" : "ms"
				}

			}
, 			{
				"box" : 				{
					"fontname" : "Lato",
					"fontsize" : 11.595186999999999,
					"id" : "obj-56",
					"maxclass" : "comment",
					"numinlets" : 1,
					"numoutlets" : 0,
					"patching_rect" : [ 633.0, 564.0, 19.0, 20.0 ],
					"text" : "|"
				}

			}
, 			{
				"box" : 				{
					"fontface" : 1,
					"fontname" : "Lato",
					"fontsize" : 12.0,
					"id" : "obj-55",
					"maxclass" : "message",
					"numinlets" : 2,
					"numoutlets" : 1,
					"outlettype" : [ "" ],
					"patching_rect" : [ 588.0, 580.0, 120.0, 23.0 ],
					"text" : "1286.054422"
				}

			}
, 			{
				"box" : 				{
					"fontname" : "Lato",
					"fontsize" : 11.595186999999999,
					"hidden" : 1,
					"id" : "obj-54",
					"maxclass" : "newobj",
					"numinlets" : 1,
					"numoutlets" : 1,
					"outlettype" : [ "" ],
					"patching_rect" : [ 465.0, 594.0, 72.0, 22.0 ],
					"text" : "prepend set"
				}

			}
, 			{
				"box" : 				{
					"fontname" : "Lato",
					"fontsize" : 11.595186999999999,
					"hidden" : 1,
					"id" : "obj-53",
					"maxclass" : "newobj",
					"numinlets" : 0,
					"numoutlets" : 1,
					"outlettype" : [ "" ],
					"patching_rect" : [ 465.0, 571.0, 90.0, 22.0 ],
					"text" : "r sampelLength"
				}

			}
, 			{
				"box" : 				{
					"fontface" : 1,
					"fontname" : "Lato",
					"fontsize" : 12.0,
					"id" : "obj-51",
					"maxclass" : "comment",
					"numinlets" : 1,
					"numoutlets" : 0,
					"patching_rect" : [ 343.0, 578.0, 36.0, 21.0 ],
					"text" : "0 ms"
				}

			}
, 			{
				"box" : 				{
					"fontname" : "Lato",
					"fontsize" : 11.595186999999999,
					"id" : "obj-50",
					"maxclass" : "comment",
					"numinlets" : 1,
					"numoutlets" : 0,
					"patching_rect" : [ 352.0, 564.0, 19.0, 20.0 ],
					"text" : "|"
				}

			}
, 			{
				"box" : 				{
					"id" : "obj-49",
					"maxclass" : "button",
					"numinlets" : 1,
					"numoutlets" : 1,
					"outlettype" : [ "bang" ],
					"parameter_enable" : 0,
					"patching_rect" : [ 245.0, 344.0, 20.0, 20.0 ]
				}

			}
, 			{
				"box" : 				{
					"fontface" : 3,
					"fontname" : "Lato",
					"fontsize" : 12.0,
					"id" : "obj-46",
					"linecount" : 3,
					"maxclass" : "comment",
					"numinlets" : 1,
					"numoutlets" : 0,
					"patching_rect" : [ 635.0, 348.0, 103.0, 50.0 ],
					"text" : "...and store and recall your own presets"
				}

			}
, 			{
				"box" : 				{
					"fontsize" : 12.754706000000001,
					"id" : "obj-45",
					"maxclass" : "preset",
					"numinlets" : 1,
					"numoutlets" : 5,
					"outlettype" : [ "preset", "int", "preset", "int", "" ],
					"patching_rect" : [ 581.0, 354.0, 53.0, 31.0 ]
				}

			}
, 			{
				"box" : 				{
					"fontname" : "Lato",
					"fontsize" : 11.595186999999999,
					"id" : "obj-44",
					"maxclass" : "message",
					"numinlets" : 2,
					"numoutlets" : 1,
					"outlettype" : [ "" ],
					"patching_rect" : [ 463.0, 370.0, 94.0, 22.0 ],
					"text" : "clear, 0 0, $1 $1"
				}

			}
, 			{
				"box" : 				{
					"addpoints" : [ 0.0, 0.0, 0, 134.430770999999993, 1286.054442999999992, 0, 165.797957999999994, 194.295989999999989, 0, 389.849243000000001, 194.295989999999989, 0, 407.773346000000004, 1175.028197999999975, 0, 622.862610000000018, 1193.532592999999906, 0, 654.229796999999962, 157.287230999999991, 0, 864.838013000000046, 157.287230999999991, 0, 954.458495999999968, 1221.289062000000058, 0, 1062.003173999999944, 1230.541259999999966, 0, 1062.003173999999944, 148.035048999999987, 0, 1286.054442999999992, 148.035048999999987, 0 ],
					"domain" : 1286.054443359375,
					"id" : "obj-43",
					"maxclass" : "function",
					"numinlets" : 1,
					"numoutlets" : 4,
					"outlettype" : [ "float", "", "", "bang" ],
					"outputmode" : 1,
					"parameter_enable" : 0,
					"patching_rect" : [ 352.0, 399.0, 299.0, 164.0 ],
					"range" : [ 0.0, 1286.054443359375 ]
				}

			}
, 			{
				"box" : 				{
					"fontname" : "Lato",
					"fontsize" : 11.595186999999999,
					"id" : "obj-42",
					"maxclass" : "newobj",
					"numinlets" : 2,
					"numoutlets" : 1,
					"outlettype" : [ "float" ],
					"patching_rect" : [ 463.0, 345.0, 30.470589, 22.0 ],
					"text" : "f"
				}

			}
, 			{
				"box" : 				{
					"fontname" : "Lato",
					"fontsize" : 11.595186999999999,
					"id" : "obj-41",
					"linecount" : 2,
					"maxclass" : "message",
					"numinlets" : 2,
					"numoutlets" : 1,
					"outlettype" : [ "" ],
					"patching_rect" : [ 352.0, 349.0, 77.0, 36.0 ],
					"text" : "domain $1, range 0. $1"
				}

			}
, 			{
				"box" : 				{
					"fontname" : "Lato",
					"fontsize" : 11.595186999999999,
					"id" : "obj-40",
					"maxclass" : "newobj",
					"numinlets" : 0,
					"numoutlets" : 1,
					"outlettype" : [ "" ],
					"patching_rect" : [ 352.0, 313.0, 90.0, 22.0 ],
					"text" : "r sampelLength"
				}

			}
, 			{
				"box" : 				{
					"fontface" : 3,
					"fontname" : "Lato",
					"fontsize" : 12.0,
					"id" : "obj-39",
					"linecount" : 2,
					"maxclass" : "comment",
					"numinlets" : 1,
					"numoutlets" : 0,
					"patching_rect" : [ 500.0, 304.0, 188.0, 35.0 ],
					"text" : "in loop mode, you can reset to normal playback..."
				}

			}
, 			{
				"box" : 				{
					"id" : "obj-38",
					"maxclass" : "button",
					"numinlets" : 1,
					"numoutlets" : 1,
					"outlettype" : [ "bang" ],
					"parameter_enable" : 0,
					"patching_rect" : [ 463.0, 300.0, 37.0, 37.0 ]
				}

			}
, 			{
				"box" : 				{
					"fontname" : "Lato",
					"fontsize" : 11.595186999999999,
					"hidden" : 1,
					"id" : "obj-37",
					"maxclass" : "newobj",
					"numinlets" : 1,
					"numoutlets" : 0,
					"patcher" : 					{
						"fileversion" : 1,
						"appversion" : 						{
							"major" : 8,
							"minor" : 5,
							"revision" : 5,
							"architecture" : "x64",
							"modernui" : 1
						}
,
						"classnamespace" : "box",
						"rect" : [ 375.0, 125.0, 175.0, 205.0 ],
						"bglocked" : 0,
						"openinpresentation" : 0,
						"default_fontsize" : 10.0,
						"default_fontface" : 0,
						"default_fontname" : "Lato",
						"gridonopen" : 1,
						"gridsize" : [ 15.0, 15.0 ],
						"gridsnaponopen" : 1,
						"objectsnaponopen" : 1,
						"statusbarvisible" : 2,
						"toolbarvisible" : 1,
						"lefttoolbarpinned" : 0,
						"toptoolbarpinned" : 0,
						"righttoolbarpinned" : 0,
						"bottomtoolbarpinned" : 0,
						"toolbars_unpinned_last_save" : 0,
						"tallnewobj" : 0,
						"boxanimatetime" : 200,
						"enablehscroll" : 1,
						"enablevscroll" : 1,
						"devicewidth" : 0.0,
						"description" : "",
						"digest" : "",
						"tags" : "",
						"style" : "",
						"subpatcher_template" : "",
						"assistshowspatchername" : 0,
						"boxes" : [ 							{
								"box" : 								{
									"fontname" : "Lato",
									"fontsize" : 11.595186999999999,
									"id" : "obj-5",
									"linecount" : 3,
									"maxclass" : "message",
									"numinlets" : 2,
									"numoutlets" : 1,
									"outlettype" : [ "" ],
									"patching_rect" : [ 91.0, 154.0, 79.0, 45.0 ],
									"text" : ";\rscrubLoop 0;\rscrubDemo 1"
								}

							}
, 							{
								"box" : 								{
									"fontname" : "Lato",
									"fontsize" : 11.595186999999999,
									"id" : "obj-4",
									"linecount" : 3,
									"maxclass" : "message",
									"numinlets" : 2,
									"numoutlets" : 1,
									"outlettype" : [ "" ],
									"patching_rect" : [ 49.0, 107.0, 79.0, 45.0 ],
									"text" : ";\rscrubLoop 1;\rscrubDemo 0"
								}

							}
, 							{
								"box" : 								{
									"fontname" : "Lato",
									"fontsize" : 11.595186999999999,
									"id" : "obj-3",
									"linecount" : 3,
									"maxclass" : "message",
									"numinlets" : 2,
									"numoutlets" : 1,
									"outlettype" : [ "" ],
									"patching_rect" : [ 7.0, 60.0, 79.0, 45.0 ],
									"text" : ";\rscrubLoop 0;\rscrubDemo 0"
								}

							}
, 							{
								"box" : 								{
									"fontname" : "Lato",
									"fontsize" : 11.595186999999999,
									"id" : "obj-2",
									"maxclass" : "newobj",
									"numinlets" : 4,
									"numoutlets" : 4,
									"outlettype" : [ "bang", "bang", "bang", "" ],
									"patching_rect" : [ 7.0, 36.0, 145.0, 20.0 ],
									"text" : "sel 2 1 0"
								}

							}
, 							{
								"box" : 								{
									"comment" : "choice",
									"id" : "obj-1",
									"index" : 1,
									"maxclass" : "inlet",
									"numinlets" : 0,
									"numoutlets" : 1,
									"outlettype" : [ "int" ],
									"patching_rect" : [ 7.0, 6.0, 25.0, 25.0 ]
								}

							}
 ],
						"lines" : [ 							{
								"patchline" : 								{
									"destination" : [ "obj-2", 0 ],
									"source" : [ "obj-1", 0 ]
								}

							}
, 							{
								"patchline" : 								{
									"destination" : [ "obj-3", 0 ],
									"source" : [ "obj-2", 0 ]
								}

							}
, 							{
								"patchline" : 								{
									"destination" : [ "obj-4", 0 ],
									"source" : [ "obj-2", 1 ]
								}

							}
, 							{
								"patchline" : 								{
									"destination" : [ "obj-5", 0 ],
									"source" : [ "obj-2", 2 ]
								}

							}
 ],
						"styles" : [ 							{
								"name" : "AudioStatus_Menu",
								"default" : 								{
									"bgfillcolor" : 									{
										"angle" : 270.0,
										"autogradient" : 0,
										"color" : [ 0.294118, 0.313726, 0.337255, 1 ],
										"color1" : [ 0.454902, 0.462745, 0.482353, 0.0 ],
										"color2" : [ 0.290196, 0.309804, 0.301961, 1.0 ],
										"proportion" : 0.39,
										"type" : "color"
									}

								}
,
								"parentstyle" : "",
								"multi" : 0
							}
 ]
					}
,
					"patching_rect" : [ 370.0, 278.0, 54.0, 22.0 ],
					"saved_object_attributes" : 					{
						"description" : "",
						"digest" : "",
						"fontname" : "Lato",
						"fontsize" : 10.0,
						"globalpatchername" : "",
						"tags" : ""
					}
,
					"text" : "p choice"
				}

			}
, 			{
				"box" : 				{
					"id" : "obj-25",
					"maxclass" : "ezdac~",
					"numinlets" : 2,
					"numoutlets" : 0,
					"patching_rect" : [ 188.0, 525.0, 45.0, 45.0 ]
				}

			}
, 			{
				"box" : 				{
					"fontname" : "Lato",
					"fontsize" : 11.595186999999999,
					"id" : "obj-24",
					"maxclass" : "newobj",
					"numinlets" : 2,
					"numoutlets" : 1,
					"outlettype" : [ "signal" ],
					"patching_rect" : [ 188.0, 498.0, 41.0, 22.0 ],
					"text" : "*~ 0.2"
				}

			}
, 			{
				"box" : 				{
					"color" : [ 0.082353, 0.431373, 0.411765, 1.0 ],
					"fontname" : "Lato",
					"fontsize" : 11.595186999999999,
					"id" : "obj-22",
					"maxclass" : "newobj",
					"numinlets" : 1,
					"numoutlets" : 2,
					"outlettype" : [ "signal", "bang" ],
					"patching_rect" : [ 188.0, 474.0, 79.0, 22.0 ],
					"text" : "play~ sampel"
				}

			}
, 			{
				"box" : 				{
					"fontname" : "Lato",
					"fontsize" : 11.595186999999999,
					"id" : "obj-21",
					"maxclass" : "newobj",
					"numinlets" : 2,
					"numoutlets" : 4,
					"outlettype" : [ "signal", "signal", "", "bang" ],
					"patching_rect" : [ 188.0, 450.0, 51.0, 22.0 ],
					"text" : "zigzag~"
				}

			}
, 			{
				"box" : 				{
					"fontname" : "Lato",
					"fontsize" : 11.595186999999999,
					"id" : "obj-20",
					"maxclass" : "newobj",
					"numinlets" : 1,
					"numoutlets" : 0,
					"patching_rect" : [ 69.661766, 564.0, 92.0, 22.0 ],
					"text" : "s sampelLength"
				}

			}
, 			{
				"box" : 				{
					"fontname" : "Lato",
					"fontsize" : 11.595186999999999,
					"id" : "obj-19",
					"maxclass" : "newobj",
					"numinlets" : 1,
					"numoutlets" : 1,
					"outlettype" : [ "bang" ],
					"patching_rect" : [ 50.0, 503.0, 58.0, 22.0 ],
					"text" : "loadbang"
				}

			}
, 			{
				"box" : 				{
					"id" : "obj-18",
					"maxclass" : "button",
					"numinlets" : 1,
					"numoutlets" : 1,
					"outlettype" : [ "bang" ],
					"parameter_enable" : 0,
					"patching_rect" : [ 24.0, 503.0, 20.0, 20.0 ]
				}

			}
, 			{
				"box" : 				{
					"color" : [ 0.945098, 0.913725, 0.407843, 1.0 ],
					"fontname" : "Lato",
					"fontsize" : 11.595186999999999,
					"id" : "obj-17",
					"maxclass" : "newobj",
					"numinlets" : 1,
					"numoutlets" : 9,
					"outlettype" : [ "float", "list", "float", "float", "float", "float", "float", "", "int" ],
					"patching_rect" : [ 24.0, 532.0, 79.882355000000004, 22.0 ],
					"text" : "info~ sampel"
				}

			}
, 			{
				"box" : 				{
					"color" : [ 0.945098, 0.913725, 0.407843, 1.0 ],
					"fontname" : "Lato",
					"fontsize" : 11.595186999999999,
					"id" : "obj-16",
					"maxclass" : "newobj",
					"numinlets" : 1,
					"numoutlets" : 2,
					"outlettype" : [ "float", "bang" ],
					"patching_rect" : [ 24.0, 465.0, 150.0, 22.0 ],
					"text" : "buffer~ sampel vibes-a1.aif"
				}

			}
, 			{
				"box" : 				{
					"fontname" : "Lato",
					"fontsize" : 11.595186999999999,
					"id" : "obj-15",
					"maxclass" : "message",
					"numinlets" : 2,
					"numoutlets" : 1,
					"outlettype" : [ "" ],
					"patching_rect" : [ 24.0, 436.0, 49.0, 22.0 ],
					"text" : "replace"
				}

			}
, 			{
				"box" : 				{
					"fontname" : "Lato",
					"fontsize" : 11.595186999999999,
					"id" : "obj-14",
					"maxclass" : "message",
					"numinlets" : 2,
					"numoutlets" : 1,
					"outlettype" : [ "" ],
					"patching_rect" : [ 134.0, 258.0, 69.0, 22.0 ],
					"text" : "loopmode 1"
				}

			}
, 			{
				"box" : 				{
					"fontname" : "Lato",
					"fontsize" : 11.595186999999999,
					"id" : "obj-11",
					"maxclass" : "message",
					"numinlets" : 2,
					"numoutlets" : 1,
					"outlettype" : [ "" ],
					"patching_rect" : [ 16.0, 356.0, 82.0, 22.0 ],
					"text" : "0, loopmode 0"
				}

			}
, 			{
				"box" : 				{
					"fontname" : "Lato",
					"fontsize" : 11.595186999999999,
					"id" : "obj-10",
					"maxclass" : "newobj",
					"numinlets" : 2,
					"numoutlets" : 1,
					"outlettype" : [ "" ],
					"patching_rect" : [ 96.0, 300.0, 33.0, 22.0 ],
					"text" : "gate"
				}

			}
, 			{
				"box" : 				{
					"fontface" : 0,
					"fontname" : "Lato",
					"fontsize" : 11.595186999999999,
					"id" : "obj-9",
					"maxclass" : "newobj",
					"numinlets" : 1,
					"numoutlets" : 3,
					"outlettype" : [ "bang", "int", "bang" ],
					"patching_rect" : [ 57.0, 228.0, 96.0, 22.0 ],
					"text" : "t b 1 b"
				}

			}
, 			{
				"box" : 				{
					"fontface" : 0,
					"fontname" : "Lato",
					"fontsize" : 11.595186999999999,
					"id" : "obj-8",
					"maxclass" : "newobj",
					"numinlets" : 1,
					"numoutlets" : 2,
					"outlettype" : [ "bang", "int" ],
					"patching_rect" : [ 16.0, 228.0, 33.0, 22.0 ],
					"text" : "t b 0"
				}

			}
, 			{
				"box" : 				{
					"fontname" : "Lato",
					"fontsize" : 11.595186999999999,
					"id" : "obj-7",
					"maxclass" : "newobj",
					"numinlets" : 3,
					"numoutlets" : 3,
					"outlettype" : [ "bang", "bang", "" ],
					"patching_rect" : [ 16.0, 203.0, 102.0, 22.0 ],
					"text" : "sel 0 1"
				}

			}
, 			{
				"box" : 				{
					"fontname" : "Lato",
					"fontsize" : 11.595186999999999,
					"id" : "obj-6",
					"maxclass" : "newobj",
					"numinlets" : 5,
					"numoutlets" : 4,
					"outlettype" : [ "int", "", "", "int" ],
					"patching_rect" : [ 215.0, 261.0, 78.0, 22.0 ],
					"text" : "counter 0 1 8"
				}

			}
, 			{
				"box" : 				{
					"fontname" : "Lato",
					"fontsize" : 11.595186999999999,
					"id" : "obj-5",
					"maxclass" : "newobj",
					"numinlets" : 1,
					"numoutlets" : 2,
					"outlettype" : [ "bang", "bang" ],
					"patching_rect" : [ 201.0, 237.0, 33.0, 22.0 ],
					"text" : "t b b"
				}

			}
, 			{
				"box" : 				{
					"fontname" : "Lato",
					"fontsize" : 11.595186999999999,
					"id" : "obj-4",
					"maxclass" : "newobj",
					"numinlets" : 2,
					"numoutlets" : 1,
					"outlettype" : [ "bang" ],
					"patching_rect" : [ 201.0, 210.0, 40.0, 22.0 ],
					"text" : "metro"
				}

			}
, 			{
				"box" : 				{
					"fontname" : "Lato",
					"fontsize" : 11.595186999999999,
					"id" : "obj-3",
					"maxclass" : "newobj",
					"numinlets" : 0,
					"numoutlets" : 1,
					"outlettype" : [ "" ],
					"patching_rect" : [ 222.0, 181.0, 90.0, 22.0 ],
					"text" : "r sampelLength"
				}

			}
, 			{
				"box" : 				{
					"fontname" : "Lato",
					"fontsize" : 11.595186999999999,
					"id" : "obj-2",
					"maxclass" : "newobj",
					"numinlets" : 0,
					"numoutlets" : 1,
					"outlettype" : [ "" ],
					"patching_rect" : [ 201.0, 154.0, 77.0, 22.0 ],
					"text" : "r scrubDemo"
				}

			}
, 			{
				"box" : 				{
					"fontname" : "Lato",
					"fontsize" : 11.595186999999999,
					"id" : "obj-1",
					"maxclass" : "newobj",
					"numinlets" : 0,
					"numoutlets" : 1,
					"outlettype" : [ "" ],
					"patching_rect" : [ 16.0, 154.0, 72.0, 22.0 ],
					"text" : "r scrubLoop"
				}

			}
, 			{
				"box" : 				{
					"background" : 1,
					"fontface" : 3,
					"fontname" : "Lato",
					"fontsize" : 20.871338000000002,
					"id" : "obj-79",
					"maxclass" : "comment",
					"numinlets" : 1,
					"numoutlets" : 0,
					"patching_rect" : [ 18.0, 11.0, 289.0, 32.0 ],
					"text" : "scrub sampler",
					"varname" : "autohelp_top_title"
				}

			}
, 			{
				"box" : 				{
					"background" : 1,
					"bgcolor" : [ 1.0, 0.788235, 0.470588, 1.0 ],
					"fontface" : 1,
					"fontsize" : 13.0,
					"hint" : "",
					"id" : "obj-93",
					"ignoreclick" : 1,
					"maxclass" : "textbutton",
					"numinlets" : 1,
					"numoutlets" : 3,
					"outlettype" : [ "", "", "int" ],
					"parameter_enable" : 0,
					"patching_rect" : [ 327.0, 536.5, 20.0, 20.0 ],
					"rounded" : 60.0,
					"text" : "1",
					"textcolor" : [ 0.34902, 0.34902, 0.34902, 1.0 ]
				}

			}
, 			{
				"box" : 				{
					"background" : 1,
					"fontface" : 3,
					"fontname" : "Lato",
					"fontsize" : 12.0,
					"id" : "obj-33",
					"linecount" : 3,
					"maxclass" : "comment",
					"numinlets" : 1,
					"numoutlets" : 0,
					"patching_rect" : [ 357.0, 135.0, 322.0, 50.0 ],
					"text" : "On the function interface, note that the horizontal axis is the real time duing playback, while the vertical axis is sample time, i.e. sample indices in the buffer~."
				}

			}
, 			{
				"box" : 				{
					"background" : 1,
					"fontface" : 3,
					"fontname" : "Lato",
					"fontsize" : 12.0,
					"id" : "obj-26",
					"linecount" : 2,
					"maxclass" : "comment",
					"numinlets" : 1,
					"numoutlets" : 0,
					"patching_rect" : [ 357.0, 92.0, 309.0, 35.0 ],
					"text" : "The scrub sampler plays back a sample using time remapping with function~>zigzag~>play~."
				}

			}
, 			{
				"box" : 				{
					"background" : 1,
					"fontface" : 3,
					"fontname" : "Lato",
					"fontsize" : 12.0,
					"id" : "obj-36",
					"linecount" : 2,
					"maxclass" : "comment",
					"numinlets" : 1,
					"numoutlets" : 0,
					"patching_rect" : [ 429.0, 235.0, 289.0, 35.0 ],
					"text" : "when in loop mode, your updates to the function are played the next time the loop comes around."
				}

			}
, 			{
				"box" : 				{
					"background" : 1,
					"fontface" : 3,
					"fontname" : "Lato",
					"fontsize" : 12.0,
					"id" : "obj-35",
					"maxclass" : "comment",
					"numinlets" : 1,
					"numoutlets" : 0,
					"patching_rect" : [ 429.0, 207.0, 279.0, 21.0 ],
					"text" : "start with the demo to get an idea how it works."
				}

			}
 ],
		"lines" : [ 			{
				"patchline" : 				{
					"destination" : [ "obj-7", 0 ],
					"source" : [ "obj-1", 0 ]
				}

			}
, 			{
				"patchline" : 				{
					"color" : [ 0.811765, 0.372549, 0.372549, 1.0 ],
					"destination" : [ "obj-49", 0 ],
					"midpoints" : [ 105.5, 326.0, 254.5, 326.0 ],
					"source" : [ "obj-10", 0 ]
				}

			}
, 			{
				"patchline" : 				{
					"color" : [ 0.082353, 0.25098, 0.431373, 1.0 ],
					"destination" : [ "obj-21", 0 ],
					"midpoints" : [ 25.5, 419.0, 197.5, 419.0 ],
					"source" : [ "obj-11", 0 ]
				}

			}
, 			{
				"patchline" : 				{
					"color" : [ 0.082353, 0.25098, 0.431373, 1.0 ],
					"destination" : [ "obj-21", 0 ],
					"midpoints" : [ 143.5, 417.0, 197.5, 417.0 ],
					"source" : [ "obj-14", 0 ]
				}

			}
, 			{
				"patchline" : 				{
					"destination" : [ "obj-16", 0 ],
					"source" : [ "obj-15", 0 ]
				}

			}
, 			{
				"patchline" : 				{
					"destination" : [ "obj-18", 0 ],
					"midpoints" : [ 164.5, 494.0, 33.5, 494.0 ],
					"source" : [ "obj-16", 1 ]
				}

			}
, 			{
				"patchline" : 				{
					"destination" : [ "obj-20", 0 ],
					"source" : [ "obj-17", 6 ]
				}

			}
, 			{
				"patchline" : 				{
					"destination" : [ "obj-17", 0 ],
					"source" : [ "obj-18", 0 ]
				}

			}
, 			{
				"patchline" : 				{
					"destination" : [ "obj-17", 0 ],
					"midpoints" : [ 59.5, 525.0, 33.5, 525.0 ],
					"source" : [ "obj-19", 0 ]
				}

			}
, 			{
				"patchline" : 				{
					"destination" : [ "obj-4", 0 ],
					"source" : [ "obj-2", 0 ]
				}

			}
, 			{
				"patchline" : 				{
					"color" : [ 0.811765, 0.372549, 0.372549, 1.0 ],
					"destination" : [ "obj-10", 1 ],
					"source" : [ "obj-21", 3 ]
				}

			}
, 			{
				"patchline" : 				{
					"destination" : [ "obj-22", 0 ],
					"source" : [ "obj-21", 0 ]
				}

			}
, 			{
				"patchline" : 				{
					"destination" : [ "obj-24", 0 ],
					"source" : [ "obj-22", 0 ]
				}

			}
, 			{
				"patchline" : 				{
					"destination" : [ "obj-25", 1 ],
					"order" : 0,
					"source" : [ "obj-24", 0 ]
				}

			}
, 			{
				"patchline" : 				{
					"destination" : [ "obj-25", 0 ],
					"order" : 1,
					"source" : [ "obj-24", 0 ]
				}

			}
, 			{
				"patchline" : 				{
					"destination" : [ "obj-4", 1 ],
					"source" : [ "obj-3", 0 ]
				}

			}
, 			{
				"patchline" : 				{
					"destination" : [ "obj-37", 0 ],
					"hidden" : 1,
					"source" : [ "obj-34", 0 ]
				}

			}
, 			{
				"patchline" : 				{
					"destination" : [ "obj-42", 0 ],
					"source" : [ "obj-38", 0 ]
				}

			}
, 			{
				"patchline" : 				{
					"destination" : [ "obj-5", 0 ],
					"source" : [ "obj-4", 0 ]
				}

			}
, 			{
				"patchline" : 				{
					"destination" : [ "obj-41", 0 ],
					"order" : 1,
					"source" : [ "obj-40", 0 ]
				}

			}
, 			{
				"patchline" : 				{
					"destination" : [ "obj-42", 1 ],
					"midpoints" : [ 361.5, 342.0, 483.970589000000018, 342.0 ],
					"order" : 0,
					"source" : [ "obj-40", 0 ]
				}

			}
, 			{
				"patchline" : 				{
					"destination" : [ "obj-43", 0 ],
					"source" : [ "obj-41", 0 ]
				}

			}
, 			{
				"patchline" : 				{
					"destination" : [ "obj-44", 0 ],
					"source" : [ "obj-42", 0 ]
				}

			}
, 			{
				"patchline" : 				{
					"destination" : [ "obj-21", 0 ],
					"midpoints" : [ 454.833333333333314, 609.0, 179.666655999999989, 609.0, 179.666655999999989, 439.0, 197.5, 439.0 ],
					"source" : [ "obj-43", 1 ]
				}

			}
, 			{
				"patchline" : 				{
					"destination" : [ "obj-43", 0 ],
					"midpoints" : [ 472.5, 396.0, 361.5, 396.0 ],
					"source" : [ "obj-44", 0 ]
				}

			}
, 			{
				"patchline" : 				{
					"destination" : [ "obj-43", 0 ],
					"midpoints" : [ 590.5, 396.0, 361.5, 396.0 ],
					"source" : [ "obj-45", 0 ]
				}

			}
, 			{
				"patchline" : 				{
					"color" : [ 0.811765, 0.372549, 0.372549, 1.0 ],
					"destination" : [ "obj-43", 0 ],
					"midpoints" : [ 254.5, 396.0, 361.5, 396.0 ],
					"source" : [ "obj-49", 0 ]
				}

			}
, 			{
				"patchline" : 				{
					"color" : [ 0.811765, 0.372549, 0.372549, 1.0 ],
					"destination" : [ "obj-49", 0 ],
					"midpoints" : [ 210.5, 319.0, 254.5, 319.0 ],
					"source" : [ "obj-5", 0 ]
				}

			}
, 			{
				"patchline" : 				{
					"destination" : [ "obj-6", 0 ],
					"source" : [ "obj-5", 1 ]
				}

			}
, 			{
				"patchline" : 				{
					"destination" : [ "obj-54", 0 ],
					"hidden" : 1,
					"source" : [ "obj-53", 0 ]
				}

			}
, 			{
				"patchline" : 				{
					"destination" : [ "obj-55", 0 ],
					"hidden" : 1,
					"midpoints" : [ 474.5, 619.0, 573.0, 619.0, 573.0, 576.0, 597.5, 576.0 ],
					"source" : [ "obj-54", 0 ]
				}

			}
, 			{
				"patchline" : 				{
					"destination" : [ "obj-61", 0 ],
					"source" : [ "obj-6", 0 ]
				}

			}
, 			{
				"patchline" : 				{
					"destination" : [ "obj-34", 0 ],
					"hidden" : 1,
					"source" : [ "obj-61", 2 ]
				}

			}
, 			{
				"patchline" : 				{
					"destination" : [ "obj-43", 0 ],
					"hidden" : 1,
					"source" : [ "obj-61", 0 ]
				}

			}
, 			{
				"patchline" : 				{
					"destination" : [ "obj-8", 0 ],
					"source" : [ "obj-7", 0 ]
				}

			}
, 			{
				"patchline" : 				{
					"destination" : [ "obj-9", 0 ],
					"source" : [ "obj-7", 1 ]
				}

			}
, 			{
				"patchline" : 				{
					"destination" : [ "obj-10", 0 ],
					"midpoints" : [ 39.5, 272.5, 105.5, 272.5 ],
					"source" : [ "obj-8", 1 ]
				}

			}
, 			{
				"patchline" : 				{
					"destination" : [ "obj-11", 0 ],
					"source" : [ "obj-8", 0 ]
				}

			}
, 			{
				"patchline" : 				{
					"destination" : [ "obj-10", 0 ],
					"midpoints" : [ 105.0, 262.5, 105.5, 262.5 ],
					"source" : [ "obj-9", 1 ]
				}

			}
, 			{
				"patchline" : 				{
					"destination" : [ "obj-14", 0 ],
					"midpoints" : [ 143.5, 256.0, 143.5, 256.0 ],
					"source" : [ "obj-9", 2 ]
				}

			}
, 			{
				"patchline" : 				{
					"color" : [ 0.811765, 0.372549, 0.372549, 1.0 ],
					"destination" : [ "obj-49", 0 ],
					"midpoints" : [ 66.5, 326.0, 254.5, 326.0 ],
					"source" : [ "obj-9", 0 ]
				}

			}
 ],
		"dependency_cache" : [  ],
		"autosave" : 0,
		"styles" : [ 			{
				"name" : "AudioStatus_Menu",
				"default" : 				{
					"bgfillcolor" : 					{
						"angle" : 270.0,
						"autogradient" : 0,
						"color" : [ 0.294118, 0.313726, 0.337255, 1 ],
						"color1" : [ 0.454902, 0.462745, 0.482353, 0.0 ],
						"color2" : [ 0.290196, 0.309804, 0.301961, 1.0 ],
						"proportion" : 0.39,
						"type" : "color"
					}

				}
,
				"parentstyle" : "",
				"multi" : 0
			}
 ],
		"bgcolor" : [ 0.886275, 0.886275, 0.886275, 1.0 ]
	}

}
