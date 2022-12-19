// add lodash script to file to get python-like modularity
let script = document.createElement("script");
script.src = "https://cdnjs.cloudflare.com/ajax/libs/lodash.js/4.17.4/lodash.js";
document.getElementsByTagName("head")[0].appendChild(script);

let inputannotexts = [];
let rightsaveddata = {}, currenttext = -1;
const LABELENUM = {0: "[B]", 1: "[C]", 2: "{U}", 3: "[U}", 4: "{U]", 5: "[R>", 6: "<R]", 7: "[<>]"};
let tmlCOUNT = 1, tmlALTCOUNTS = {};
let LASTIDNUM = 0;
let do_popup = true;

function keyselectlabel(event) {
    console.log("keyselectlabel");
    //console.log(event);
    if (event.keyCode === 8 || event.keyCode === 65 || event.keyCode === 88) // backspace, a, x
        event.stopPropagation();
    if (event.keyCode === 32) //spacebar
        event.stopPropagation();
    if (event.keyCode === 13) { //enter
        event.stopPropagation();
        updatetimeline();
    }
    let usehotkeys = true;
    if (usehotkeys) {
        let key = event.keyCode || event.which;
        if (key === 66) {
            if (document.getElementById("0typeselect").checked)
                document.getElementById("1typeselect").checked = true;
            else
                document.getElementById("0typeselect").checked = true;
        } else if (key === 83) {
            if (document.getElementById("1typeselect").checked)
                document.getElementById("0typeselect").checked = true;
            else
                document.getElementById("1typeselect").checked = true;
        } else if (key === 82) {
            if (document.getElementById("6typeselect").checked)
                document.getElementById("5typeselect").checked = true;
            else
                document.getElementById("6typeselect").checked = true;
        } else if (key === 85) {
            if (document.getElementById("2typeselect").checked)
                document.getElementById("4typeselect").checked = true;
            else if (document.getElementById("4typeselect").checked)
                document.getElementById("3typeselect").checked = true;
            else
                document.getElementById("2typeselect").checked = true;
        } else if (key === 73) {
            document.getElementById("7typeselect").checked = true;
        } else if (key === 84) {    //coref keyinputs
            document.getElementById("0corefselect").checked = true;
        } else if (key === 69) {    //coref keyinputs
            document.getElementById("1corefselect").checked = true;
        }
    }
}

function focusBar(ev) {
    console.log('focusBar');
    document.getElementById(parseInt(ev.target.id) + "rlistinput1").focus();
}

function focusBarFactuality(ev) {
    console.log('focusBarFactuality');
    document.getElementById(parseInt(ev.target.id) + "rlistinput2").focus();
}

let focusCorefHighlightList = {};

function focusText(ev) {
    console.log("focusText");
    updatetimeline();
    switch (parseInt(document.querySelector('input[name="chooseInterface"]:checked').value)) {
        case 0:
            let focusCorefKey;
            if (document.getElementById(parseInt(ev.target.id) + "rcoref").value === "")
                focusCorefKey = parseInt(ev.target.id);
            else
                focusCorefKey = parseInt(document.getElementById(parseInt(ev.target.id) + "rcoref").value);
            if (focusCorefHighlightList.hasOwnProperty(focusCorefKey)) {
                focusCorefHighlightList[focusCorefKey].forEach(function (id) {
                    document.getElementById(parseInt(id) + "mark").style.backgroundColor = "#EC9D50";
                });
            }
            break;
        case 1:
        case 2:
            document.getElementById(parseInt(ev.target.id) + "mark").style.backgroundColor = "#EC9D50";
            break;
    }
    document.getElementById(parseInt(ev.target.id) + "mark").scrollIntoView({behavior: 'smooth', block: 'center'});
    document.getElementById(parseInt(ev.target.id) + "rlisttext").style.backgroundColor = "#EC9D50";
    let point = document.getElementById(parseInt(ev.target.id) + "point"),
        bar = document.getElementById(parseInt(ev.target.id) + "bar");
    if (point !== null) {
        point.style.backgroundColor = "#EC9D50";
    }
    if (bar !== null) {
        bar.style.borderColor = "#EC9D50";
    }
}

function blurText(ev) {
    console.log("blurText");
    switch (parseInt(document.querySelector('input[name="chooseInterface"]:checked').value)) {
        case 0:
            updaterightlist();
            let focusCorefKey;
            if (document.getElementById(parseInt(ev.target.id) + "rcoref").value === "")
                focusCorefKey = parseInt(ev.target.id);
            else
                focusCorefKey = parseInt(document.getElementById(parseInt(ev.target.id) + "rcoref").value);
            if (focusCorefHighlightList.hasOwnProperty(focusCorefKey)) {
                focusCorefHighlightList[focusCorefKey].forEach(function (id) {
                    document.getElementById(parseInt(id) + "mark").style.backgroundColor = "";
                });
            }
            break;
        case 1:
        case 2:
            document.getElementById(parseInt(ev.target.id) + "mark").style.backgroundColor = "";
            break;
    }
    document.getElementById(parseInt(ev.target.id) + "rlisttext").style.backgroundColor = "";
    updatetimeline();
}

function cycleType(ev) {
    console.log("cycleType");
    let id = parseInt(ev.target.id),
        button = document.getElementById(id + "rlistbutton"),
        newtype = (parseInt(button.getAttribute("data-type")) + 1) % 8;
    if (newtype === 5 || newtype === 6)
        newtype = 7;
    button.setAttribute("data-type", newtype);
    button.innerText = LABELENUM[newtype];
    document.getElementById(id + "label").innerText = LABELENUM[newtype];
    switch (newtype) {
        case 0:
        case 1:
            button.style.backgroundColor = "#94618e";
            break;
        case 2:
        case 3:
        case 4:
            button.style.backgroundColor = "#67AB9F";
            break;
        case 5:
        case 6:
            button.style.backgroundColor = "lightcoral";
            break;
        case 7:
            button.style.backgroundColor = "#EC9D50";
            break;
        default:
            button.style.backgroundColor = "lightgrey";
            break;
    }


}

function getRandomPastelColor() {
    console.log('getRandomPastelColor');
    let h = Math.floor(Math.random() * (360 - 1) + 1);
    let s = 100;
    let l = 70;
    return 'hsl(' + h + ',' + s + '%,' + l + '%)';
}

function getRandomColorFromList() {
    console.log('getRandomColorFromList');
    let goodColors = ["hsl(357, 37%, 42%)", "hsl(357, 43%, 57%)", "hsl(357, 83%, 74%)", "hsl(357, 28%, 54%)", "hsl(357, 35%, 69%)", "hsl(355, 31%, 41%)"];
    return goodColors[Math.floor(Math.random() * goodColors.length)];
}

function getSetColorFromList(num) {
    console.log('getSetColorFromList');
    let goodColors = ["hsl(357, 37%, 42%)", "hsl(357, 43%, 57%)", "hsl(357, 83%, 74%)", "hsl(357, 28%, 54%)", "hsl(357, 35%, 69%)", "hsl(355, 31%, 41%)"];
    return goodColors[num % goodColors.length];
}

// arrow border color should ideally be "hsl(357, 47%, 30%)" or #70282C, but the color border really determines the whole color at the moment


////////////////////////////

function clearList() {
    do_popup = false;

    console.log("clearList");
    let marks = document.getElementsByTagName("mark");

    let textbox = document.getElementById("righttextbox");
    for (let i = marks.length - 1; i >= 0; --i) {
        marks[i].click();
    }
    document.getElementById("righteventlist").innerHTML = "";

    tmlCOUNT = 1;
    tmlALTCOUNTS = {};

    updatetimeline();
    do_popup = true;
}

function loadText() {
    console.log('loadText');
    clearList();
    document.getElementById(currenttext + "textselector").selected = true;
    document.getElementById("0typeselect").checked = true;
    document.getElementById("1corefselect").checked = true;
    rightpanelsetup(rightsaveddata[currenttext]["text"]);

    switch (parseInt(document.querySelector('input[name="chooseInterface"]:checked').value)) {
        case 0:
            if (typeof (rightsaveddata[currenttext]["events"]) !== 'undefined') {
                let corefmap = {};
                if (rightsaveddata[currenttext].hasOwnProperty("event_coreference")) {
                    Object.keys(rightsaveddata[currenttext]["event_coreference"]).forEach(function (key) {
                        rightsaveddata[currenttext]["event_coreference"][key].forEach(function (value) {
                            corefmap[value] = key;
                        });
                    });
                }
                Object.values(rightsaveddata[currenttext]["events"]).forEach(function (ev_order_obj) {
                    let range = document.createRange(),
                        firstwordpos = ev_order_obj[0],
                        lastwordpos = ev_order_obj[1];
                    range.setStart(document.querySelector('[data-idx="' + firstwordpos + '"]').childNodes[0], 0);
                    range.setEnd(document.querySelector('[data-idx="' + lastwordpos + '"]').childNodes[0], 1);
                    if ([].concat(arrayfromselection(range.cloneContents().children)).some(function (element) {
                        return element.innerText.indexOf('\n') !== -1;
                    }))
                        range.setEnd(document.querySelector('[data-idx="' + (lastwordpos + 1) + '"]').childNodes[0], 1);
                    if ([].concat(arrayfromselection(range.cloneContents().children)).some(function (element) {
                        return "MARK" === element.tagName;
                    }))
                        return false;
                    if (range.commonAncestorContainer.nodeName === "MARK")
                        return false;
                    newselection(range, ev_order_obj["type"]);
                    newlistitem(firstwordpos, {
                        coref: corefmap.hasOwnProperty(firstwordpos) ? corefmap[firstwordpos] : ""
                    });
                    return true;

                });
            }
            if (typeof (rightsaveddata[currenttext]["timex"]) !== 'undefined') {
                Object.values(rightsaveddata[currenttext]["timex"]).forEach(function (timex_obj) {
                        let range = document.createRange(),
                            firstwordpos = timex_obj[0],
                            lastwordpos = timex_obj[1];
                        range.setStart(document.querySelector('[data-idx="' + firstwordpos + '"]').childNodes[0], 0);
                        range.setEnd(document.querySelector('[data-idx="' + lastwordpos + '"]').childNodes[0], 1);
                        if ([].concat(arrayfromselection(range.cloneContents().children)).some(function (element) {
                            return element.innerText.indexOf('\n') !== -1;
                        }))
                            range.setEnd(document.querySelector('[data-idx="' + (lastwordpos + 1) + '"]').childNodes[0], 1);
                        if ([].concat(arrayfromselection(range.cloneContents().children)).some(function (element) {
                            return "MARK" === element.tagName;
                        }))
                            return false;
                        if (range.commonAncestorContainer.nodeName === "MARK")
                            return false;
                        newselection(range, timex_obj["type"], true);
                        return true;
                    }
                );
            }
            break;
        case 2:
            leftpanelsetup();
        case 1:
            if (typeof (rightsaveddata[currenttext]["event_order"]) !== 'undefined') {
                Object.values(rightsaveddata[currenttext]["event_order"]).forEach(function (ev_order_obj) {
                    let range = document.createRange(),
                        firstwordpos = ev_order_obj["span"][0],
                        lastwordpos = ev_order_obj["span"][1];
                    range.setStart(document.querySelector('[data-idx="' + firstwordpos + '"]').childNodes[0], 0);
                    range.setEnd(document.querySelector('[data-idx="' + lastwordpos + '"]').childNodes[0], 1);
                    if ([].concat(arrayfromselection(range.cloneContents().children)).some(function (element) {
                        return element.innerText.indexOf('\n') !== -1;
                    }))
                        range.setEnd(document.querySelector('[data-idx="' + (lastwordpos + 1) + '"]').childNodes[0], 1);
                    if ([].concat(arrayfromselection(range.cloneContents().children)).some(function (element) {
                        return "MARK" === element.tagName;
                    }))
                        return false;
                    if (range.commonAncestorContainer.nodeName === "MARK")
                        return false;
                    newselection(range, ev_order_obj["type"]);
                    newlistitem(firstwordpos, {
                        type: ev_order_obj["type"],
                        i1: ev_order_obj["time"],
                        i2: ev_order_obj["factuality"],
                        i3: ev_order_obj["branch"]
                    });
                    return true;

                });
            }
            break;
    }
    updatetimeline();
}

function loadPrev() {
    console.log('loadPrev');
    saveEventOrder();
    if (currenttext === parseInt(Object.keys(rightsaveddata)[Object.keys(rightsaveddata).length - 1])) {
        //document.getElementsByClassName("prevnextbutton")[1].disabled = false;
        document.getElementById("nextbutton").disabled = false;

    }
    --currenttext;
    if (currenttext <= 0) {
        //document.getElementsByClassName("prevnextbutton")[0].disabled = true;
        document.getElementById("prevbutton").disabled = true;
    }
    loadText();
}

function loadNext() {
    console.log('loadNext');
    saveEventOrder();
    if (currenttext === 0) {
        //document.getElementsByClassName("prevnextbutton")[0].disabled = false;
        document.getElementById("prevbutton").disabled = false;
    }
    ++currenttext;
    if (currenttext >= parseInt(Object.keys(rightsaveddata)[Object.keys(rightsaveddata).length - 1])) {
        //document.getElementsByClassName("prevnextbutton")[1].disabled = true;
        document.getElementById("nextbutton").disabled = true;
    }
    loadText();
}

function loadFromList(ev) {
  console.log('loadFromList');
  
    saveEventOrder();
    currenttext = parseInt(ev.target.value);
    document.getElementById("prevbutton").disabled = (currenttext === 0); //prev
    document.getElementById("nextbutton").disabled = (currenttext >= parseInt(Object.keys(rightsaveddata)[Object.keys(rightsaveddata).length - 1]));
    
    // console.log(parseInt(Object.keys(rightsaveddata)[Object.keys(rightsaveddata).length - 1]));
    // console.log(parseInt(currenttext));
    // console.log(document.getElementsByClassName("prevnextbutton")[1].disabled);

    // console.log(document.getElementsByClassName("prevnextbutton"));
    
    loadText();
}

function newlistitem(wordpos, inputline) {
    console.log("newlistitem");
    let selectiontext = document.getElementById(wordpos + "mark"),
        listcontainer = document.createElement("div"),
        listtext = document.createElement("div"),
        inputtoselect;
    switch (parseInt(document.querySelector('input[name="chooseInterface"]:checked').value)) {
        case 0:
            console.log('case 0');
            let eventid = document.createElement("input"),
                coref = document.createElement("input");

            listcontainer.id = wordpos + "rlistcontainer";
            listcontainer.className = "rlistcontainer";

            listtext.id = wordpos + "rlisttext";
            listtext.className = ("rlisttext" + (parseInt(document.querySelector('input[name="corefselect"]:checked').value) ? "" : " rlisttextblue"));
            for (let i = 0; i < selectiontext.childNodes.length; ++i) {
                listtext.appendChild(selectiontext.childNodes[i].cloneNode(true));
            }

            eventid.id = wordpos + "reventid";
            eventid.className = "rlistinput rcoref rcorefevid";
            eventid.value = wordpos.toString();
            eventid.setAttribute("onfocus", "focusText(event)");
            eventid.setAttribute("onblur", "blurText(event)");
            eventid.readOnly = true;

            coref.id = wordpos + "rcoref";
            coref.className = "rlistinput rcoref rcorefcolor";
            coref.setAttribute("onfocus", "focusText(event)");
            coref.setAttribute("onblur", "blurText(event)");
            coref.value = inputline["coref"];

            listcontainer.appendChild(listtext);
            listcontainer.appendChild(eventid);
            listcontainer.appendChild(coref);

            inputtoselect = coref;

            break;
        case 1:
        case 2:
            console.log('case 2');
            let listbutton = document.createElement("button"),
                listinput1 = document.createElement("input"),
                listinput2 = document.createElement("input"),
                listinput3 = document.createElement("input");

            listcontainer.id = wordpos + "rlistcontainer";
            listcontainer.className = "rlistcontainer";

            listtext.id = wordpos + "rlisttext";
            listtext.className = "rlisttext";
            for (let i = 0; i < selectiontext.childNodes.length - 1; ++i) {
                listtext.appendChild(selectiontext.childNodes[i].cloneNode(true));
            }

            listbutton.id = wordpos + "rlistbutton";
            listbutton.className = "rlistbutton";
            listbutton.setAttribute("data-type", inputline.type);
            listbutton.innerText = LABELENUM[parseInt(inputline.type)];
            listbutton.setAttribute("onclick", "cycleType(event)");
            switch (parseInt(inputline.type)) {
                case 0:
                case 1:
                    listbutton.style.backgroundColor = "#94618e";
                    break;
                case 2:
                case 3:
                case 4:
                    listbutton.style.backgroundColor = "#67AB9F";
                    break;
                case 5:
                case 6:
                    listbutton.style.backgroundColor = "lightcoral";
                    break;
                case 7:
                    listbutton.style.backgroundColor = "#EC9D50";
                    break;
                default:
                    listbutton.style.backgroundColor = "lightgrey";
                    break;
            }

            listinput1.id = wordpos + "rlistinput1";
            listinput1.className = "rlistinput";
            listinput1.value = inputline.i1;
            listinput1.setAttribute("onfocus", "focusText(event)");
            listinput1.setAttribute("onblur", "blurText(event)");

            if (inputline.i3 === "") {
                listinput1.onchange = function (ev) {
                    if (!isNaN(parseInt(ev.target.value)))
                        tmlCOUNT = parseInt(ev.target.value) + 1;
                };
            } else {
                listinput1.onchange = function (ev) {
                    if (!isNaN(parseInt(ev.target.value)))
                        tmlALTCOUNTS[inputline.i3] = parseInt(ev.target.value) + 1;
                };
            }

            listinput2.id = wordpos + "rlistinput2";
            listinput2.className = "rlistinput";
            listinput2.value = inputline.i2;
            listinput2.setAttribute("onfocus", "focusText(event)");
            listinput2.setAttribute("onblur", "blurText(event)");

            listinput3.id = wordpos + "rlistinput3";
            listinput3.className = "rlistinput rli3";
            if ("i3" in inputline)
                listinput3.value = inputline.i3;
            listinput3.setAttribute("onfocus", "focusText(event)");
            listinput3.setAttribute("onblur", "blurText(event)");

            listcontainer.appendChild(listtext);
            listcontainer.appendChild(listbutton);
            listcontainer.appendChild(listinput1);
            listcontainer.appendChild(listinput3);
            listcontainer.appendChild(listinput2);

            //add the item to the list in the correct position by wordpos
            let list = document.getElementsByClassName("rlistcontainer"),
                beenadded = false;
            for (let i = 0; i < list.length; i++) {
                if (parseInt(list[i].id) > wordpos) {
                    list[i].parentElement.insertBefore(listcontainer, list[i]);
                    beenadded = true;
                    break;
                }
            }
            if (!beenadded)
                document.getElementById("righteventlist").appendChild(listcontainer);
            inputtoselect = listinput1;
            break;
    }

    //add the item to the list in the correct position by wordpos
    let list = document.getElementsByClassName("rlistcontainer"),
        beenadded = false;
    for (let i = 0; i < list.length; i++) {
        if (parseInt(list[i].id) > wordpos) {
            list[i].parentElement.insertBefore(listcontainer, list[i]);
            beenadded = true;
            break;
        }
    }
    if (!beenadded)
        document.getElementById("righteventlist").appendChild(listcontainer);
    inputtoselect.focus();
}

function removelistitem(wordpos) {
    console.log("removelistitem");
    console.log(parseInt(wordpos));
    let toremove = document.getElementById(parseInt(wordpos) + "rlistcontainer");
    toremove.parentNode.removeChild(toremove);
}   

function confirmdeletion(istimex, newmark, selectedwords, textbox){
    
    return function(){
        console.log('confirmdeletion');
        console.log(do_popup);
        if (do_popup){  
            //confirm with user for deletion
            var modal = document.getElementById("myModal");
            var yesspan = document.getElementsByClassName("yes")[0];
            var nospan = document.getElementsByClassName("no")[0];

            modal.style.display = "block";
            //remove highlight on click
            yesspan.onclick = function() {
                if (istimex) {
                    selectedwords.forEach(function (word) {
                        return textbox.insertBefore(word, newmark);
                    });
                    textbox.removeChild(newmark);
                    return;
                }
                removelistitem(parseInt(newmark.id));
                if (!document.getElementById("choosecoref").checked && parseInt(newmark.id) === LASTIDNUM)
                    --tmlCOUNT;
                selectedwords.forEach(function (word) {
                    return textbox.insertBefore(word, newmark);
                }),
                    textbox.removeChild(newmark);
                updatetimeline();
                modal.style.display = "none";
            }
    
            nospan.onclick = function() {
                modal.style.display = "none";
            }
        }
        else{
            if (istimex) {
                selectedwords.forEach(function (word) {
                    return textbox.insertBefore(word, newmark);
                });
                textbox.removeChild(newmark);
                return;
            }
            removelistitem(parseInt(newmark.id));
            if (!document.getElementById("choosecoref").checked && parseInt(newmark.id) === LASTIDNUM)
                --tmlCOUNT;
            selectedwords.forEach(function (word) {
                return textbox.insertBefore(word, newmark);
            }),
                textbox.removeChild(newmark);
            updatetimeline();
        }
    }
    
}

function newselection(selectionrange, labelnum = document.querySelector('input[name="typeselect"]:checked').value, istimex = false) {
    console.log("newselection");
    //console.log(labelnum);
    let textbox = document.getElementById("righttextbox");
    // new text was selected:
    let initiallabel = LABELENUM[labelnum],
        firstselectedword = selectionrange.startContainer.parentElement,
        lastselectedword = selectionrange.endContainer.parentElement,
        firstwordpos = parseInt(firstselectedword.getAttribute("data-idx")),
        lastwordpos = parseInt(lastselectedword.getAttribute("data-idx")),
        newmark = document.createElement("mark");

    if (labelnum === 5 || labelnum === 6 || labelnum==7)
        initiallabel = LABELENUM[0];

    //add mark to doc
    console.log("adding mark");
    newmark.id = firstwordpos + "mark";
    if (istimex)
        newmark.className = "timexmark";

    textbox.insertBefore(newmark, firstselectedword);
    newmark.scrollIntoView({behavior: 'smooth', block: 'center'}); //make it scroll only if needed?

    let selectedwords = _.range(firstwordpos, lastwordpos + 1).map(function (wordpos) {
        return document.querySelector('[data-idx="' + wordpos + '"]');
    });

    selectedwords.forEach(function (word) {
        return newmark.appendChild(word);
    }),
        (newmark.innerHTML += !document.getElementById("choosecoref").checked ? ('<span id=' + firstwordpos + "label" + ' class="label">' + initiallabel + '</span>') : ''),
        newmark.addEventListener("click", confirmdeletion(istimex, newmark, selectedwords, textbox)),
        0;
}

function arrayfromselection(selectedelements) {
    console.log('arrayfromselection');
    if (Array.isArray(selectedelements)) {
        let i, j;
        for (i = 0, j = Array(selectedelements.length); i < selectedelements.length; i++) j[i] = selectedelements[i];
        return j;
    }
    return Array.from(selectedelements);
}

function rightpanelsetup(text) {
    console.log('rightpanelsetup');
    // set up text
    let textbox = document.getElementById("righttextbox");
    tmlCOUNT = 1;
    tmlALTCOUNTS = {};

    console.log(rightsaveddata);

    //AG: To show only first event of an event-coref cluster
    let hascoref = {}; //{event:1} if the event is part of some coref cluster 
    var allowed = []; //first event of each coref cluster is allowed
    let eventlist = rightsaveddata[currenttext]["events"];
    if (typeof eventlist!== 'undefined'){
        for (let i = 0; i < Object.keys(eventlist).length; ++i) {
            hascoref[eventlist[i][0]] = 0;
        }
    }
    
    let corefmap = {};
    if (rightsaveddata[currenttext].hasOwnProperty("event_coreference")) {
        Object.keys(rightsaveddata[currenttext]["event_coreference"]).forEach(function (key) {
            min_event = key;
            rightsaveddata[currenttext]["event_coreference"][key].forEach(function (value) {
                corefmap[value] = key;
                hascoref[key] = 1;
                hascoref[value] = 1;
                min_event = Math.min(value, min_event); //first event of a coref cluster
                allowed.push(min_event);
            });
        });
    }

   // console.log(allowed);
   // console.log(hascoref);

    //map spans to event numbers
    let eventmap = {}, timexmap = {};
    let invisible = [];
    
    if (rightsaveddata[currenttext].hasOwnProperty("events") && typeof rightsaveddata[currenttext]["events"] !== 'undefined') {
        let eventmapeventlist = rightsaveddata[currenttext]["events"];
        
        for (let i = 0; i < Object.keys(eventlist).length; ++i) {
            //AG: commenting as it does not include events that are present in corefmap.
            //if (corefmap.hasOwnProperty(eventlist[i][0]) && corefmap[eventlist[i][0]] !== eventlist[i][0]) continue;
            
            
            //AG: if the event is part of some coref cluster but is not the first event, don't show the event. continue.
            if (hascoref[eventlist[i][0]]==1 && allowed.includes(eventlist[i][0])==false){
                console.log(eventlist[i][0]);
                invisible.push(eventlist[i][0]);
                continue;
            }
            if (eventlist[i][0] === eventlist[i][1]){
                eventmap[eventlist[i][0]] = "both";
            }
            else {
                eventmap[eventlist[i][0]] = "start";
                eventmap[eventlist[i][1]] = "stop";
            }
            for (let j = eventlist[i][0] + 1; j <= eventlist[i][1] - 1; ++j)
                eventmap[j] = "middle";
        }
        
        rightsaveddata[currenttext]["invisible_events"] = invisible; //AG: add invisible events to data (to be exported).
    }
    if (rightsaveddata[currenttext].hasOwnProperty("timex") && typeof rightsaveddata[currenttext]["timex"] !== 'undefined') {
        let timexlist = rightsaveddata[currenttext]["timex"];
        for (let i = 0; i < Object.keys(timexlist).length; ++i) {
            if (timexlist[i][0] === timexlist[i][1])
                timexmap[timexlist[i][0]] = "both";
            else {
                timexmap[timexlist[i][0]] = "start";
                timexmap[timexlist[i][1]] = "stop";
            }
            for (let j = timexlist[i][0] + 1; j <= timexlist[i][1] - 1; ++j)
                timexmap[j] = "middle";
        }
    }
    console.log(eventmap);

    (textbox.innerHTML = text.split(' ').map(function (word, wordposition) {
        // let texttoadd = "";
        // if(typeof eventmap[wordposition] !== 'undefined'){
        //     texttoadd = ' style="background-color:' + getSetColorFromList(eventmap[wordposition]) + '" '
        // }
        switch (parseInt(document.querySelector('input[name="chooseInterface"]:checked').value)) {
            case 0:
                return '<span data-idx="' + wordposition + '">' + word + ' </span>';
            case 1:
            case 2:
                //console.log(eventmap);
                //console.log(wordposition);
                //console.log(typeof eventmap[wordposition]); //string
                //console.log(rightsaveddata[currenttext].hasOwnProperty("event_coreference")); //true
                //console.log(Object.values(rightsaveddata[currenttext]["event_coreference"]).some(function (list){
                //    list.includes(wordposition)})); //false

                if (typeof eventmap[wordposition] !== 'undefined' && (!rightsaveddata[currenttext].hasOwnProperty("event_coreference"))) {
                    //AG: if event_coreference field is not specified, show all events
                    console.log('entering the [] condition.')
                    if (eventmap[wordposition] === "both")
                        word = '[' + word + ']';
                    else if (eventmap[wordposition] === "start")
                        word = '[' + word;
                    else if (eventmap[wordposition] === "stop")
                        word = word + ']';
                }
                else if (typeof eventmap[wordposition] !== 'undefined' && (rightsaveddata[currenttext].hasOwnProperty("event_coreference")
                        && !Object.values(rightsaveddata[currenttext]["event_coreference"]).some(function (list){
                            list.includes(wordposition);
                    }))) {
                    //AG: if event_coreference field is specified, do filtering
                    
                    if (eventmap[wordposition] === "both")
                        word = '[' + word + ']';
                    else if (eventmap[wordposition] === "start")
                        word = '[' + word;
                    else if (eventmap[wordposition] === "stop")
                        word = word + ']';
                }
                if (typeof timexmap[wordposition] !== 'undefined') {
                    if (timexmap[wordposition] === "both")
                        word = '[' + word + ']';
                    else if (timexmap[wordposition] === "start")
                        word = '[' + word;
                    else if (timexmap[wordposition] === "stop")
                        word = word + ']';
                }
                let classname = "";
                if (typeof eventmap[wordposition] !== 'undefined')
                    classname = "textevent";
                else if (typeof timexmap[wordposition] !== 'undefined')
                    classname = "timexevent";
                else classname = "notimexortext";
                return '<span class=' + classname
                    + ' data-idx="' + wordposition + '">' + word + ' </span>';
        }
    }).join("")), textbox.addEventListener("mouseup", function () {
        let selection = window.getSelection();
        if (!selection.isCollapsed) {
            let selectionrange = selection.getRangeAt(0);

            //if there is already a mark in the selection deselect and return
            if ([].concat(arrayfromselection(selectionrange.cloneContents().children)).some(function (element) {
                return "MARK" === element.tagName;
            }))
                return selection.removeAllRanges();//, void button card .focus(); not sure if card should be included
            //in seperate function to allow handling of matching annotations
            let wordpos = parseInt(selectionrange.startContainer.parentElement.getAttribute("data-idx"));

            switch (parseInt(document.querySelector('input[name="chooseInterface"]:checked').value)) {
                case 0:
                    if (parseInt(document.querySelector('input[name="corefselect"]:checked').value)) {
                        newselection(selectionrange, 0, false);
                        newlistitem(wordpos, {id: wordpos});
                    } else {
                        newselection(selectionrange, 0, true);
                    }
                    break;
                case 1:
                case 2:
                    let labelnum = parseInt(document.querySelector('input[name="typeselect"]:checked').value);
                    let i1text;
                    if (labelnum === 5 || labelnum === 6) {
                        let i3text = (labelnum === 6 ? "<" : "") + (tmlCOUNT - 1) + (labelnum === 5 ? ">" : "");
                        i1text = "";
                        if (i3text in tmlALTCOUNTS)
                            i1text = (tmlALTCOUNTS[i3text]++).toString();
                        else {
                            i1text = "1";
                            tmlALTCOUNTS[i3text] = 2;
                        }
                        newselection(selectionrange, 0);
                        newlistitem(wordpos, {i1: i1text, i2: "", i3: i3text, type: 0})
                    } else { // mapping unbounded inputs to timeline vals
                        if (labelnum === 2 || labelnum === 3 || labelnum === 4)
                            i1text = (tmlCOUNT === 1 ? 1 : (tmlCOUNT - 1)).toString();
                        else
                            i1text = labelnum === 7 ? ":" : tmlCOUNT.toString();
                        newselection(selectionrange);
                        newlistitem(wordpos, {i1: i1text, i2: "", i3: "", type: labelnum});
                        if (labelnum === 0 || labelnum === 1) {
                            ++tmlCOUNT;
                            LASTIDNUM = wordpos;
                        }
                    }
                    break;
            }
        }
    });
}

function updatetimeline() {
    console.log('updatetimeline');

    updaterightlist();

    if (document.getElementById("choosecoref").checked) return;
    document.getElementById("righttimeline").innerHTML = "";
    let list = Array.from(document.getElementsByClassName("rlistcontainer"));

    let reltllists = {"": {points: [], bars: []}}, barlists = {};
    list.forEach(function (item) {
        let reltlval = item.children[3].value,
            type = parseInt(item.children[1].getAttribute("data-type")),
            tmlval = item.children[2].value,
            tmllist = tmlval.match(/[-+]?[0-9]*\.?[0-9]+/g) === null ? [] : tmlval.match(/[-+]?[0-9]*\.?[0-9]+/g).slice(0, 2),
            speechval = item.children[4].value,
            speechlist = speechval.match(/[-+]?[0-9]*\.?[0-9]+/g) === null ? [] : speechval.match(/[-+]?[0-9]*\.?[0-9]+/g).slice(0, 2),
            ispoint = (type === 1 || type === 0) && (tmllist.length === 1 || (tmllist.length > 1 && tmllist[0] === tmllist[1])),
            isirr = (type === 7);
        if (!(reltlval in reltllists)) {
            reltllists[reltlval] = {points: [], bars: []};
        }

        //console.log(reltllists);

        reltllists[reltlval][ispoint ? "points" : "bars"].push({
            isspeech: false,
            speech: item.children[4].value,
            speechlist: speechlist,
            type: type,
            tmllist: tmllist,
            tmlval: tmlval,
            relval: reltlval,
            ispoint: ispoint,
            isirr: isirr,
            text: item.children[0].innerText,
            id: parseInt(item.id)
        });//add obj to push
    });
    let mins = {}, maxs = {};
    Object.keys(reltllists).forEach(function (key) {
        //console.log(key);
        let returnvals = createTLbars(reltllists[key], key);
        barlists[key] = returnvals[0];
        mins[key] = returnvals[1];
        maxs[key] = returnvals[2];
    });
    barlists[""].forEach(function (bar) {
        if (bar.id.includes("bar")) {
            let placeholder = document.createElement("div");
            placeholder.id = "placeholder";
            document.getElementById("righttimeline").appendChild(placeholder);
        }
        document.getElementById("righttimeline").appendChild(bar);
    });
    if (document.getElementById("placeholder") === null) {
        let placeholder = document.createElement("div");
        placeholder.id = "placeholder";
        document.getElementById("righttimeline").appendChild(placeholder);
    }
    delete barlists[""];

    //add additional timelines
    let relpointusedlist = [];
    Object.keys(barlists).forEach(function (key, index) {
        //create new essentially point
        let rellist = key.match(/[-+]?[0-9]*\.?[0-9]+/g) === null ? [] : key.match(/[-+]?[0-9]*\.?[0-9]+/g).slice(0, 2);
        if (rellist.length > 0) {
            let relpoint = document.createElement("div");
            if (key.includes('<')) {
                relpoint.className = "arrow arleft";
                relpoint.style.borderRightColor = rightlistrelcolors[key];
            } else {
                relpoint.className = "arrow arright";
                relpoint.style.borderLeftColor = rightlistrelcolors[key];
            }
            let min = parseFloat(document.getElementById("rtlstartmark").innerText),
                max = parseFloat(document.getElementById("rtlendmark").innerText);

            let leftpos;
            if (rellist[0] < min) leftpos = min;
            else if (rellist[0] > max) leftpos = max;
            else leftpos = rellist[0];

            relpoint.style.left = "calc(" + maptorange5to95(max, min, leftpos) + "% - 5px)";
            if (!(relpointusedlist.includes(leftpos)) && index > 0) {
                relpointusedlist.push(leftpos);
                //point.style.top = "-10px";
                relpoint.style.marginTop = "-10px";
            } else relpointusedlist = [leftpos];
            document.getElementById("righttimeline").insertBefore(relpoint, document.getElementById("placeholder"));

            //AG: adds tool tip to bar
            let tooltiptlkey = document.createElement("div");

            let tooltip = document.createElement("div");
            let tttlmin = document.createElement("div");
            let tttlmax = document.createElement("div");

            tooltiptlkey.className = "tttlkey";
            tooltiptlkey.appendChild(tttlmin);
            tooltiptlkey.appendChild(tttlmax);

            tttlmin.innerText = mins[key];
            tttlmax.innerText = maxs[key];
            tooltip.appendChild(tooltiptlkey);

            tooltip.className = "tooltiptimeline";
            barlists[key].forEach(function (bar) {
                tooltip.appendChild(bar);
            });

            // AG: Create the button element for the tooltip
            let tooltipCloseButton = document.createElement("button");
            tooltipCloseButton.id = "tooltip-close-button";
            tooltipCloseButton.innerText = "Close";

            let tippyInstance = tippy(relpoint, {
                content: tooltip,
                interactive: true,
                maxWidth: 2000, 
                trigger: 'click'
            });

            // AG: Create a container element for the tooltip and button
            let tooltipContainer = document.createElement("div");
            tooltipContainer.appendChild(tooltip);
            tooltipContainer.appendChild(tooltipCloseButton);

            // AG: Set the content of the tippy instance to the container element
            tippyInstance.setContent(tooltipContainer);

            // AG: Add an event listener to the button that hides the tooltip when clicked
            tooltipCloseButton.addEventListener("click", function() {
                tippy.hideAll();
            });            
        }
    })
}

function maptorange5to95(smax, smin, input) {
    return 90 / (smax - smin) * (input - smin) + 5;
}

function maptorange1to99(smax, smin, input) {
    return 98 / (smax - smin) * (input - smin) + 1;
}

function createTLbars(objlist, key, isleft = false) {
    console.log('createTLbars');
    //console.log(objlist);

    //console.log(objlist.bars);

    let points = objlist.points, bars = objlist.bars, both = points.concat(bars);
    let numlist = [];
    for (let i = 0; i < both.length; ++i)
        numlist = numlist.concat(both[i].tmllist.concat(both[i].speechlist));
    //console.log(numlist);
    let min = Math.min.apply(null, numlist), max = Math.max.apply(null, numlist);
    if (min === max) max += 1;

    if (key === "") {
        document.getElementById("rtlstartmark").innerText = min.toString();
        document.getElementById("rtlendmark").innerText = max.toString();
    }
    let barlist = [], pointlist = [];
    let left = 0, right = 0;
    let tippycontentlist = {}, skiplist = [];

    //run through bars and points
    for (let i = 0; i < both.length; ++i) {
        let obj = both[i];
        if (obj.speech !== "" && !obj.isspeech) {
            if (obj.speechlist.length > 0) {
                if (obj.speechlist.length > 1) {
                    bars.push({
                        isspeech: true,
                        speech: obj.speech,
                        speechlist: [],
                        type: 0,
                        tmllist: obj.speechlist,
                        tmlval: obj.tmlval,
                        ispoint: false,
                        text: obj.text,
                        id: obj.id
                    });
                }
                if (obj.speechlist.length === 1) {
                    points.push({
                        isspeech: true,
                        speech: obj.speech,
                        speechlist: [],
                        type: 0,
                        tmllist: obj.speechlist,
                        tmlval: obj.tmlval,
                        ispoint: true,
                        text: obj.text,
                        id: obj.id
                    });
                }
            }
        }
    }

    for (let i = 0; i < bars.length; ++i) {
        let obj = bars[i];
        if (skiplist.includes(i)) continue;
        // if (obj.type === 7) {
        //     skiplist.push(i);
        //     continue;
        // }
        tippycontentlist[i] = (!obj.isspeech ? (LABELENUM[obj.type] + " " + obj.tmlval) : "[Factuality]") + " " + obj.speech + " " + obj.text;
        for (let j = i + 1; j < bars.length; ++j) {
            let obj2 = bars[j];
            if ((LABELENUM[obj.type] === LABELENUM[obj2.type] && obj.tmlval.match(/[!@#$%^&*]+/) !== null && obj.tmlval === obj2.tmlval && obj.speech === obj2.speech)
                || (obj.isspeech && obj2.isspeech && LABELENUM[obj.type] === LABELENUM[obj2.type] && obj.speech === obj2.speech)) {
                skiplist.push(j);
                tippycontentlist[i] = tippycontentlist[i] + " <...> " + obj2.text;
            }
        }
    }
    //console.log(tippycontentlist);

    for (let i = 0; i < bars.length; ++i) {
        if (skiplist.includes(i)) continue;
        let bar = document.createElement("div"), obj = bars[i];
        barlist.push(bar);
        bar.className = "listbar";
        bar.id = obj.id + "bar";
        if (!isleft)
            bar.setAttribute("onclick", obj.isspeech ? "focusBarFactuality(event)" : "focusBar(event)");

        tippy(bar, {content: tippycontentlist[i]});

        //console.log('casing for bars');
        //console.log(obj.type);
        switch (obj.type) {
            case 0:
                left = maptorange5to95(max, min, obj.tmllist[0]);
                right = maptorange5to95(max, min, obj.tmllist[1]);
                bar.style.backgroundColor = obj.isspeech ? "#348092" : "#94618e";
                break;
            case 1:
                left = maptorange5to95(max, min, obj.tmllist[0]);
                right = maptorange5to95(max, min, obj.tmllist[1]);
                bar.style.backgroundColor = obj.isspeech ? "#348092" : "#94618e";
                break;
            case 2:
                left = 0;
                right = 100;
                bar.style.backgroundColor = "#67AB9F";
                for (let j = 0; j < obj.tmllist.length; ++j) {
                    let marker = document.createElement("div");
                    bar.appendChild(marker);
                    marker.className = "statemarker";
                    marker.style.left = "calc(" + maptorange5to95(max, min, obj.tmllist[j]) + "% - 5px)";
                }
                break;
            case 3:
                left = maptorange5to95(max, min, obj.tmllist[0]);
                right = 100;
                bar.style.backgroundColor = "#67AB9F";
                break;
            case 4:
                left = 0;
                right = maptorange5to95(max, min, obj.tmllist[obj.tmllist.length - 1]);
                bar.style.backgroundColor = "#67AB9F";
                break;
            case 7:
                //console.log(obj.relval);
                if (obj.relval===""){
                    break;
                }
                else{
                    let rellist = obj.relval.match(/[-+]?[0-9]*\.?[0-9]+/g).slice(0, 2)
                    left = maptorange5to95(max, min, rellist[0]);
                    right = maptorange5to95(max, min, rellist[1]);
                    bar.style.backgroundColor = obj.isspeech ? "#348092" : "#94618e";
                    break;
                }
                
                //left = maptorange5to95(max, min, obj.tmllist[0]);
                //right = maptorange5to95(max, min, obj.tmllist[1]);
                //bar.style.backgroundColor = obj.isspeech ? "#348092" : "#94618e";
                //break;
            default:
                break;
        }
        //console.log(left);
        //console.log(right);

        bar.style.left = left + "%";
        bar.style.width = (right - left) + "%";

        if (obj.speech.includes('@')) {
            bar.className += " listbarspeech"
        }
    }
    //creates top row with points
    let pointusedlist = [];
    skiplist = [];
    tippycontentlist = {};
    for (let i = 0; i < points.length; ++i) {
        let obj = points[i];
        if (skiplist.includes(i)) continue;
        tippycontentlist[i] = (!obj.isspeech ? (LABELENUM[obj.type] + " " + obj.tmlval) : "[Factuality]") + " " + obj.speech + " " + obj.text;
        for (let j = i + 1; j < points.length; ++j) {
            let obj2 = points[j];
            if ((LABELENUM[obj.type] === LABELENUM[obj2.type] && obj.tmlval.match(/[!@#$%^&*]+/) !== null && obj.tmlval === obj2.tmlval && obj.speech === obj2.speech)
                || (obj.isspeech && obj2.isspeech && LABELENUM[obj.type] === LABELENUM[obj2.type] && obj.speech === obj2.speech)) {
                skiplist.push(j);
                tippycontentlist[i] = tippycontentlist[i] + " <...> " + obj2.text;
            }
        }
    }
    for (let i = 0; i < points.length; ++i) {
        if (skiplist.includes(i)) continue;
        let point = document.createElement("div"), obj = points[i];
        pointlist.push(point);
        point.className = "listpoint";
        point.id = obj.id + "point";
        if (!isleft)
            point.setAttribute("onclick", obj.isspeech ? "focusBarFactuality(event)" : "focusBar(event)");

        tippy(point, {content: tippycontentlist[i]});

        point.style.left = "calc(" + maptorange5to95(max, min, obj.tmllist[0]) + "% - 5px)";
        if (!(pointusedlist.includes(obj.tmllist[0])) && i > 0) {
            pointusedlist.push(obj.tmllist[0]);
            //point.style.top = "-10px";
            point.style.marginTop = "-10px";
        } else pointusedlist = [obj.tmllist[0]];

        if (obj.isspeech) {
//            point.style.backgroundColor = "#829DA3";
            point.style.borderColor = "#0B839F";
        }

        if (obj.speech.includes('@')) {
            point.className += " listpointspeech"
        }
    }

    //returns list of elements
    return [pointlist.concat(barlist), min, max];
}

let rightlistrelcolors = {};
let factualityVals = new Set(['-', "m", "m-"]);

function updaterightlist() {
    console.log('updaterightlist');
    switch (parseInt(document.querySelector('input[name="chooseInterface"]:checked').value)) {
        case 0:
            rightlistrelcolors = {"": ""};
            focusCorefHighlightList = {};
            let coreflist = document.getElementsByClassName("rcorefcolor");
            for (let i = 0; i < coreflist.length; i++) {
                coreflist[i].value = coreflist[i].value.match(/[-+]?[0-9]*\.?[0-9]+/) === null ? "" : coreflist[i].value.match(/[-+]?[0-9]*\.?[0-9]+/);
                if (parseInt(coreflist[i].id) === parseInt(coreflist[i].value))
                    coreflist[i].value = "";
                if (!(coreflist[i].value in rightlistrelcolors))
                    rightlistrelcolors[coreflist[i].value] = getSetColorFromList(i);
                coreflist[i].style.backgroundColor = rightlistrelcolors[coreflist[i].value];
                if (!focusCorefHighlightList.hasOwnProperty(coreflist[i].value))
                    focusCorefHighlightList[coreflist[i].value] = [];
                focusCorefHighlightList[coreflist[i].value].push(coreflist[i].id);
            }
            let evidlist = document.getElementsByClassName("rcorefevid");
            for (let i = 0; i < evidlist.length; i++) {
                if (evidlist[i].value in rightlistrelcolors)
                    evidlist[i].style.backgroundColor = rightlistrelcolors[evidlist[i].value];
                else
                    evidlist[i].style.backgroundColor = "";
                if (!focusCorefHighlightList.hasOwnProperty(evidlist[i].value))
                    focusCorefHighlightList[evidlist[i].value] = [];
                focusCorefHighlightList[evidlist[i].value].push(evidlist[i].value);
            }
            break;
        case 1:
        case 2:
            //correct tml, correct rel_to, correct speech
            let containerlist = document.getElementsByClassName("rlistcontainer");
            for (let i = 0; i < containerlist.length; i++) {
                //containerlist[0].children[0] = text, 1 = type, 2 = tml, 3 = relto, 4 = speech
                let textelement = containerlist[i].children[0],
                    typebutton = containerlist[i].children[1],
                    tmlinput = containerlist[i].children[2],
                    reltoinput = containerlist[i].children[3],
                    speechinput = containerlist[i].children[4];

                //cleans up tml
                let newval, tmllist;
                //console.log(parseInt(typebutton.getAttribute("data-type")));
                //console.log(newval);
                switch (parseInt(typebutton.getAttribute("data-type"))) {
                    case 0:
                    case 1:
                        tmllist = tmlinput.value.match(/[-+]?[0-9]*\.?[0-9]+/g) === null ? [] : tmlinput.value.match(/[-+]?[0-9]*\.?[0-9]+/g).slice(0, 2);
                        if (tmllist.length < 1)
                            newval = "0";
                        else if (tmllist.length > 1)
                            newval = tmllist[0] + ":" + tmllist[1];
                        else newval = tmllist[0];
                        break;
                    case 2: //{}
                    case 3:
                    case 4:
                        tmllist = tmlinput.value.match(/[-+]?[0-9]*\.?[0-9]+/g) === null ? [] : tmlinput.value.match(/[-+]?[0-9]*\.?[0-9]+/g).slice(0, 2);
                        if (tmllist.length < 1)
                            newval = ":";
                        else if (tmllist.length > 1)
                            newval = tmllist[0] + ":" + tmllist[1];
                        else newval = tmllist[0];
                        break;
                    case 7:
                        tmllist = tmlinput.value.match(/[-+]?[0-9]*\.?[0-9]+/g) === null ? [] : tmlinput.value.match(/[-+]?[0-9]*\.?[0-9]+/g).slice(0, 2);
                        if (tmllist.length < 1)
                            newval = "1";
                        else if (tmllist.length > 1)
                            newval = tmllist[0] + ":" + tmllist[1];
                        else newval = tmllist[0];
                        break;
                }
                if (tmlinput.value.match(/[!@#$%^&*]+/) !== null) newval += tmlinput.value.match(/[!@#$%^&*]+/);
                tmlinput.value = newval;

                //cleans up rel_to
                newval = "";
                //console.log(reltoinput.value);
                if (reltoinput.value.match(/[<:>]/)=== null) {
                    newval = "";
                    //console.log('null');
                } 
                else{
                    let rellist = reltoinput.value.match(/[-+]?[0-9]*\.?[0-9]+/g).slice(0, 2);
                    if (rellist.length < 1)
                        newval = "1";
                    else if (rellist.length > 1)
                        newval = rellist[0] + ":" + rellist[1];
                    else newval = rellist[0];

                    if (reltoinput.value.includes('<')) {
                        newval = '<' + reltoinput.value.match(/[-+]?[0-9]*\.?[0-9]+/);
                        //console.log('< condition');
                    } 
                    else if (reltoinput.value.includes('>')){
                        newval = reltoinput.value.match(/[-+]?[0-9]*\.?[0-9]+/) + '>';
                        //console.log('> condition');
                    }
                    if (reltoinput.value.match(/[!@#$%^&*]+/) !== null){
                        //console.log('last if');
                        newval += reltoinput.value.match(/[!@#$%^&*]+/);
                    }
                }
                reltoinput.value = newval;

                // if (reltoinput.value.match(/[<>]/) === null || reltoinput.value.match(/[-+]?[0-9]*\.?[0-9]+/) === null) {
                //     newval = "";
                //     console.log('if condition');
                // }  
                // else {
                //     if (reltoinput.value.includes(':')) {
                //         newval = reltoinput.value[0] + ":" + reltoinput.value[1];
                //         console.log(': condition');
                //     } 
                //     if (reltoinput.value.includes('<')) {
                //         newval = '<' + reltoinput.value.match(/[-+]?[0-9]*\.?[0-9]+/);
                //         console.log('< condition');
                //     } 
                //     else{
                //         newval = reltoinput.value.match(/[-+]?[0-9]*\.?[0-9]+/) + '>';
                //         console.log('> condition');
                //     }
                //     if (reltoinput.value.match(/[!@#$%^&*]+/) !== null){
                //         console.log('last if');
                //         newval += reltoinput.value.match(/[!@#$%^&*]+/);
                //     }
                // }
                // reltoinput.value = newval;
                //console.log(reltoinput.value);


                //cleans up speech
                tmllist = speechinput.value.match(/[-+]?[0-9]*\.?[0-9]+/g) === null ? [] : speechinput.value.match(/[-+]?[0-9]*\.?[0-9]+/g).slice(0, 2);
                if (factualityVals.has(speechinput.value) === false) {
                    speechinput.value = "";
                }
            }

            rightlistrelcolors = {"": ""};
            let rellist = document.getElementsByClassName("rli3");
            for (let i = 0; i < rellist.length; i++) {
                if (!(rellist[i].value in rightlistrelcolors))
                    rightlistrelcolors[rellist[i].value] = getSetColorFromList(i);
                rellist[i].style.backgroundColor = rightlistrelcolors[rellist[i].value];
            }
            break;
    }
}

//// toggling legend display
function showLegend() {
    console.log('showLegend');
    let legend = document.getElementById("popup");
    if (legend.style.display === "none") {
        legend.style.display = "inline-block";
    } else {
        legend.style.display = "none";
    }
}


function saveEventOrder() {
    
    console.log('saveEventOrder');
    console.log('before updatetimeline');
    console.log(rightsaveddata);
    updatetimeline();
    console.log('after updatetimeline');
    console.log(rightsaveddata);
    //console.log(text.substring(1, 4));
    let events = document.getElementsByClassName("rlistcontainer");
    switch (parseInt(document.querySelector('input[name="chooseInterface"]:checked').value)) {
        case 0:
            if (rightsaveddata.length < 1 || currenttext < 0 || currenttext >= rightsaveddata.length) return;
            rightsaveddata[currenttext]["events"] = {};
            rightsaveddata[currenttext]["event_coreference"] = {};
            rightsaveddata[currenttext]["timex"] = {};
            for (let i = 0; i < events.length; ++i) {
                rightsaveddata[currenttext]["events"][i] = [parseInt(events[i].id), parseInt(events[i].id) + events[i].childNodes[0].childNodes.length - 1];
                if (events[i].childNodes[2].value !== "") {
                    if (rightsaveddata[currenttext]["event_coreference"].hasOwnProperty(events[i].childNodes[2].value))
                        rightsaveddata[currenttext]["event_coreference"][events[i].childNodes[2].value].push(parseInt(events[i].id));
                    else
                        rightsaveddata[currenttext]["event_coreference"][events[i].childNodes[2].value] = [parseInt(events[i].id)];
                }
            }
            let timexelements = document.getElementsByClassName("timexmark");
            for (let i = 0; i < timexelements.length; ++i) {
                rightsaveddata[currenttext]["timex"][i] = [parseInt(timexelements[i].id), parseInt(timexelements[i].id) + timexelements[i].childNodes.length - 1];
            }

            break;
        case 1:
        case 2:
            if (rightsaveddata.length < 1 || currenttext < 0 || currenttext >= rightsaveddata.length) return;
            text = rightsaveddata[currenttext]['text'];
            rightsaveddata[currenttext]["event_order"] = {};
            
            //AG: changing terminology 
            for (let i = 0; i < events.length; ++i) {
                rightsaveddata[currenttext]["event_order"][i] = {
                    span: [parseInt(events[i].id), parseInt(events[i].id) + events[i].childNodes[0].childNodes.length - 1],
                    type: parseInt(events[i].childNodes[1].getAttribute("data-type")),
                    time: events[i].childNodes[2].value,
                    branch: events[i].childNodes[3].value,
                    factuality: events[i].childNodes[4].value
                };

                //AG: fix for change in span boundaries when text contains '\n'
                let start = rightsaveddata[currenttext]["event_order"][i]['span'][0];
                let end = rightsaveddata[currenttext]["event_order"][i]['span'][1];
                let tokens = text.split(' ');
                let span_text = tokens.slice(start,end).join(" ");
                if (span_text.includes('\n')){
                    rightsaveddata[currenttext]["event_order"][i]['span'][1] = rightsaveddata[currenttext]["event_order"][i]['span'][1]-1;
                }
               
            }
            break;
    }
}

function loadJsonlFile(ev) {
    console.log('loadJsonlFile');
    let reader;
    switch (parseInt(document.querySelector('input[name="chooseInterface"]:checked').value)) {
        case 0:
        case 1:
            clearList();
            let file = ev.target.files[0];
            reader = new FileReader();
            reader.readAsText(file, 'UTF-8');
            reader.onload = readerEvent => {
                let content = readerEvent.target.result;
                content = content.trim();
                content = content.split('\n');
                content = content.map(line => JSON.parse(line));
                addFirstFile(content);
            };
            break;
        case 2:
            clearList();
            let files = ev.target.files[0];
            reader = new FileReader();
            reader.readAsText(files, 'UTF-8');
            reader.onload = readerEvent => {
                let content = readerEvent.target.result;
                content = content.trim();
                content = content.split('\n');
                content = content.map(line => JSON.parse(line));
                addFirstFile(content);
            };
            break;
    }
    ev.target.value = null;
}

function addFirstFile(content) {
    console.log('addFirstFile');
    currenttext = -1;
    document.getElementById("righttextbox").innerHTML = "";
    inputannotexts = [];
    inputannotexts.push(content);
    //document.getElementsByClassName("prevnextbutton")[1].disabled = false; //next
    document.getElementById("nextbutton").disabled = false;

    //document.getElementsByClassName("prevnextbutton")[0].disabled = true; //prev
    document.getElementById("prevbutton").disabled = true;

    document.getElementById("textselect").innerHTML = "<option id=\"textselectiondefault\" value=\"\" selected disabled hidden>Choose a text to annotate</option>";
    rightsaveddata = {};
    
    Object.keys(inputannotexts[0]).forEach(function (key, index) {
            var keys = Object.keys(inputannotexts[0][key]);
            if (inputannotexts[0][key].hasOwnProperty("event_order") && parseInt(document.querySelector('input[name="chooseInterface"]:checked').value) === 1){
                rightsaveddata[index] = {'id':'', 'text':'', 'events':{}, 'event_order':{}, 'timex':{}, 'event_coreference':{}, 'invisible_events':[]};
                keys.forEach((k, i) => {
                    rightsaveddata[index][k] = inputannotexts[0][key][k];
                }
                );
            }   
            else {
                rightsaveddata[index] = {'id':'', 'text':'', 'events':{}, 'event_order':{}, 'timex':{}, 'event_coreference':{}, 'invisible_events':[]};
                keys.forEach((k, i) => {
                rightsaveddata[index][k] = inputannotexts[0][key][k];
                }
                );
            }

            if(content[key].hasOwnProperty("event_coreference")){
                rightsaveddata[index]["event_coreference"] = content[key]["event_coreference"];
            }
            if(content[key].hasOwnProperty("annotators")){
                rightsaveddata[index]["annotators"] = content[key]["annotators"];
            }
            if (content[key].hasOwnProperty("a1")) {
                rightsaveddata[index]["a1"] = content[key]["a1"];
            }
            if (content[key].hasOwnProperty("a2")) {
                rightsaveddata[index]["a2"] = content[key]["a2"];
            }
            let option = document.createElement("option");
            option.innerText = inputannotexts[0][key].hasOwnProperty("id") ? inputannotexts[0][key].id : index;
            option.value = index.toString();
            option.id = index.toString() + "textselector";
            document.getElementById("textselect").appendChild(option);
        }
    );
    console.log(rightsaveddata);
}

function exportJsonlFile() {
    console.log('exportJsonlFile');
    saveEventOrder();
    let text = Object.values(rightsaveddata).map(val => JSON.stringify(val).replace('\n', '\\n')).join('\n').replace(/([^\r])\n/g, "$1\r\n");
    let textBlob = new Blob([text], {type: 'text/plain'});
    let fileName = 'export_annotations.jsonl';
    let downloadLink = document.createElement('a');
    downloadLink.download = fileName;
    downloadLink.innerHTML = "Download File";
    if (window.webkitURL != null)
        downloadLink.href = window.webkitURL.createObjectURL(textBlob);
    else {
        downloadLink.href = window.URL.createObjectURL(textBlob);
        downloadLink.onclick = document.body.removeChild(event.target);
        downloadLink.style.display = "none";
        document.body.appendChild(downloadLink);
    }
    downloadLink.click();
}

function adjudicationMakeSelection(span0, span1, type, tml, speech, relto) {
    console.log("adjudicationMakeSelection");
    let range = document.createRange(),
        firstwordpos = span0,
        lastwordpos = span1;
    range.setStart(document.querySelector('[data-idx="' + firstwordpos + '"]').childNodes[0], 0);
    range.setEnd(document.querySelector('[data-idx="' + lastwordpos + '"]').childNodes[0], 1);
    if ([].concat(arrayfromselection(range.cloneContents().children)).some(function (element) {
        return element.innerText.indexOf('\n') !== -1;
    }))
        range.setEnd(document.querySelector('[data-idx="' + (lastwordpos + 1) + '"]').childNodes[0], 1);
    if ([].concat(arrayfromselection(range.cloneContents().children)).some(function (element) {
        return "MARK" === element.tagName;
    }))
        return false;
    if (range.commonAncestorContainer.nodeName === "MARK")
        return false;
    newselection(range, type);
    newlistitem(firstwordpos, {
        type: type,
        i1: tml,
        i2: speech,
        i3: relto
    });
    return true;
}

function leftpanelsetup() {
    console.log("leftpanelsetup");
    //files 1, 2 inputannotexts[0][currenttext], inputannotexts[1][currenttext];
    if (currenttext < 0) return;

    let a1 = rightsaveddata[currenttext]["a1"], a2 = rightsaveddata[currenttext]["a2"];
    // the code in the following line doesn't work;
    let annotatorNames = rightsaveddata[currenttext].hasOwnProperty("annotators") ? rightsaveddata[currenttext]["annotators"] : ["a1", "a2"];
    
    // hardcoding for the tests
    //let annotatorNames = ["Carmela", "Sehar"];
    let minmax = [];
    let minmaxlist = [0];
    let templist = [];

    if (rightsaveddata[currenttext].hasOwnProperty("event_order") && typeof (rightsaveddata[currenttext]["event_order"]) !== 'undefined') {
        templist = templist.concat(Object.values(rightsaveddata[currenttext]["event_order"]));
    }
    if (rightsaveddata[currenttext].hasOwnProperty("a1") && typeof (rightsaveddata[currenttext]["a1"]) !== 'undefined') {
        Object.values(a1).forEach(function (item) {
            templist = templist.concat(Object.values(item));
        });
    }
    if (rightsaveddata[currenttext].hasOwnProperty("a2") && typeof (rightsaveddata[currenttext]["a2"]) !== 'undefined') {
        Object.values(a2).forEach(function (item) {
            templist = templist.concat(Object.values(item));
        });
    }

    //console.log(templist);

    templist.forEach(function (value) {
        if (value["branch"] === '') {
            minmaxlist = minmaxlist.concat(value["time"].match(/[-+]?[0-9]*\.?[0-9]+/g) === null ? [] : value["time"].match(/[-+]?[0-9]*\.?[0-9]+/g).slice(0, 2));
        } else {
            //console.log(value);
            minmaxlist.push(value["branch"].match(/[-+]?[0-9]*\.?[0-9]+/));
        }
    });
    minmax.push(Math.min(...minmaxlist));
    minmax.push(Math.max(...minmaxlist));

    document.getElementById("leftpanel").innerHTML = "";

    if (Object.values(a1).length !== Object.values(a2).length) {
        console.log("Error, mismatched chunk lengths");
    }

    for (let i = 0; i < Object.values(a1).length; ++i) {
        let chunk = document.createElement("div");
        chunk.id = i + "lchunk";
        chunk.className = "lchunk";
        document.getElementById("leftpanel").appendChild(chunk);

        let chunktext = document.createElement("p");
        let spanmin = Object.values(Object.values(a1)[i])[0]["span"][0],
            spanmax = Object.values(Object.values(a1)[i])[0]["span"][1];
        chunktext.className = "lchunktext";
        chunk.appendChild(chunktext);


        [a1, a2].forEach(function (a, index) {
            //Object.values(a)[i];

            // div for displaying the annotator code
            let annotatorCode = document.createElement("div");
            annotatorCode.className = "annotatorCode";
            annotatorCode.innerText = annotatorNames[index];
            chunk.appendChild(annotatorCode);

            let chunktimeline = document.createElement("div");
            chunktimeline.className = "lchunktml";
            chunk.appendChild(chunktimeline);

            //onclick event added
            chunktimeline.onclick = function () {
                let offset = prompt("Please enter an integer offset:", "0"), offsetnum = 0;
                if (offset !== null) {
                    if (offset === "")
                        offsetnum = 0;
                    else
                        offsetnum = parseInt(offset);

                    Object.values(Object.values(a)[i]).forEach(function (obj) {
                        let newval, tmllist;
                        switch (parseInt(obj.type)) {
                            case 0:
                            case 1:
                                tmllist = obj.tml.match(/[-+]?[0-9]*\.?[0-9]+/g) === null ? [] : obj.tml.match(/[-+]?[0-9]*\.?[0-9]+/g).slice(0, 2);
                                if (tmllist.length < 1)
                                    newval = offsetnum.toString();
                                else if (tmllist.length > 1)
                                    newval = (parseInt(tmllist[0]) + offsetnum) + ":" + (parseInt(tmllist[1]) + offsetnum);
                                else newval = (parseInt(tmllist[0]) + offsetnum).toString();
                                break;
                            case 2: //{}
                                tmllist = obj.tml.match(/[-+]?[0-9]*\.?[0-9]+/g) === null ? [] : obj.tml.match(/[-+]?[0-9]*\.?[0-9]+/g).slice(0, 2);
                                if (tmllist.length < 1)
                                    newval = ":";
                                else if (tmllist.length > 1)
                                    newval = (parseInt(tmllist[0]) + offsetnum) + ":" + (parseInt(tmllist[1]) + offsetnum);
                                else newval = (parseInt(tmllist[0]) + offsetnum);
                                break;
                            case 3:
                                newval = obj.tml.match(/[-+]?[0-9]*\.?[0-9]+/) === null ? offsetnum.toString() : (parseInt(obj.tml.match(/[-+]?[0-9]*\.?[0-9]+/)) + offsetnum);
                                break;
                            case 4: //{]
                                tmllist = obj.tml.match(/[-+]?[0-9]*\.?[0-9]+/g) === null ? [] : obj.tml.match(/[-+]?[0-9]*\.?[0-9]+/g).slice(0, 2);
                                if (tmllist.length < 1)
                                    newval = offsetnum.toString();
                                else newval = tmllist[tmllist.length - 1];
                                break;
                            case 7:
                                newval = ":";
                                break;
                        }
                        if (obj.tml.match(/[!@#$%^&*]+/) !== null) newval += obj.tml.match(/[!@#$%^&*]+/);
                        console.log(obj.speech);
                        console.log(obj.factuality);
                        adjudicationMakeSelection(obj.span[0], obj.span[1], obj.type, newval, obj.speech, obj.relto);
                    });
                }

            };

            //timeline added
            let toCreateTL = {"points": [], "bars": []};
            Object.values(Object.values(a)[i]).forEach(function (arritem) {
                let type = arritem["type"],
                    tmlval = arritem["time"],
                    tmllist = tmlval.match(/[-+]?[0-9]*\.?[0-9]+/g) === null ? [] : tmlval.match(/[-+]?[0-9]*\.?[0-9]+/g).slice(0, 2),
                    speechval = arritem["factuality"],
                    speechlist = speechval.match(/[-+]?[0-9]*\.?[0-9]+/g) === null ? [] : speechval.match(/[-+]?[0-9]*\.?[0-9]+/g).slice(0, 2),
                    ispoint = (type === 1 || type === 0) && (tmllist.length === 1 || (tmllist.length > 1 && tmllist[0] === tmllist[1])),
                    isirr = (type === 7);

                let nbtinnertext = "";
                let splittext = rightsaveddata[currenttext]["text"].split(' ');
                for (let i = arritem["span"][0]; i <= arritem["span"][1]; ++i)
                    nbtinnertext += splittext[i] + " ";

                toCreateTL[ispoint ? "points" : "bars"].push({
                    isspeech: false,
                    speech: speechval,
                    speechlist: speechlist,
                    type: type,
                    tmllist: tmllist,
                    tmlval: tmlval,
                    ispoint: ispoint,
                    isirr: isirr,
                    text: nbtinnertext,
                    id: arritem["span"][0]
                });//add obj to push

                if (spanmin > arritem["span"][0]) spanmin = arritem["span"][0];
                if (spanmax < arritem["span"][1]) spanmax = arritem["span"][1];
            });
            createTLbars(toCreateTL, "", true)[0].forEach(function (bar) {
                chunktimeline.appendChild(bar);
            });

        });

        let nbtinnertext = "";
        let splittext = rightsaveddata[currenttext]["text"].split(' ');
        for (let i = spanmin; i <= spanmax; ++i)
            nbtinnertext += splittext[i] + " ";

        chunktext.innerText = nbtinnertext;
    }

}

let curchecked = "";

function changeInterface(radio) {
  console.log('changeInterface');
    document.getElementById("importfilebutton").disabled = false;
    if (curchecked === "" || confirm("Are you sure you want to change annotation type and delete unexported changes?")) {
        curchecked = document.querySelector('input[name="chooseInterface"]:checked').id;
        clearList();
        document.getElementById("righttextbox").innerHTML = "";
        document.getElementById("righttimeline").innerHTML = "";
        rightsaveddata = {};
        inputannotexts = [];
        currenttext = -1;
        //document.getElementsByClassName("prevnextbutton")[1].disabled = true; //next
        document.getElementById("nextbutton").disabled = true;

        //document.getElementsByClassName("prevnextbutton")[0].disabled = true; //prev
        document.getElementById("prevbutton").disabled = true;

        document.getElementById("textselectiondefault").selected = true;
        switch (parseInt(document.querySelector('input[name="chooseInterface"]:checked').value)) {
            case 0:
                document.getElementById("leftpanel").style.display = "none";

                document.getElementById("righttypesboxrow1").style.display = "";
                document.getElementById("righttypesboxrow0").style.display = "none";

                document.getElementById("relkbutton").style.display = "none";
                document.getElementById("relkpos").style.display = "none";
                document.getElementById("relktml").style.display = "none";
                document.getElementById("relk@").style.display = "none";
                document.getElementById("relkcorefeventid").style.display = "";
                document.getElementById("relkcoref").style.display = "";
                break;
            case 1:
                document.getElementById("leftpanel").style.display = "none";

                document.getElementById("righttypesboxrow1").style.display = "none";
                document.getElementById("righttypesboxrow0").style.display = "";

                //change the key
                document.getElementById("relkbutton").style.display = "";
                document.getElementById("relkpos").style.display = "";
                document.getElementById("relktml").style.display = "";
                document.getElementById("relk@").style.display = "";
                document.getElementById("relkcorefeventid").style.display = "none";
                document.getElementById("relkcoref").style.display = "none";
                break;
            case 2:
                document.getElementById("leftpanel").style.display = "flex";

                document.getElementById("righttypesboxrow1").style.display = "none";
                document.getElementById("righttypesboxrow0").style.display = "";

                //change the key
                document.getElementById("relkbutton").style.display = "";
                document.getElementById("relkpos").style.display = "";
                document.getElementById("relktml").style.display = "";
                document.getElementById("relk@").style.display = "";
                document.getElementById("relkcorefeventid").style.display = "none";
                document.getElementById("relkcoref").style.display = "none";
                break;
        }
    } else {
        radio.checked = false;
        document.getElementById(curchecked).checked = true;
    }
}

document.getElementById("chooseevent").click();
