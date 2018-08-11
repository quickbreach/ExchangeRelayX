//EmailSummary
//Subject
//Sender Name
//Date
//Has Attachments




ASYNC_LOCKED = false; 	//Every call is asychronous, so let's lock it

function lockAsync()
{
	ASYNC_LOCKED = true;
	$(".loader").show();
}
function unlockAsync()
{
	ASYNC_LOCKED = false;
	$(".loader").hide();
}
//Keep track of what folder/subfolder is selected for highlighting
function folder_highliter(folder)
{
	if($(folder).hasClass("selected")) { return;}
	for(let i = 0; i < $("li.viewMail_Distinguished_action.selected").length; i++)
	{
		var tmp = $("li.viewMail_Distinguished_action.selected")[i];
		$(tmp).removeClass("selected");
	}
	for(let i = 0; i < $("li.viewMail_FolderId_action.selected").length; i++)
	{
		var tmp = $("li.viewMail_FolderId_action.selected")[i];
		$(tmp).removeClass("selected");
	}
	$(folder).addClass("selected");
}
function email_highliter(email)
{
	console.log("Highlighting email")
	if($(email).hasClass("selected")) { return;}
	for(let i = 0; i < $("div.emailListBox.selected").length; i++)
	{
		var tmp = $("div.emailListBox.selected")[i];
		$(tmp).removeClass("selected");
	}
	$(email).addClass("selected");
}

//1. Clears the column
//Takes in a list of  emailListBox's and appends/prepends the HTML
function load_column(listOfEmails, clearColumn = true)
{
	return;
}


/* Core back-end request functions */

//Gets a list of subfolders and loads it in the left (note: nested sub-folders won't be shown, I need to add recursion to the expandAllSubFolders operation)	
function load_subfolders(callback = null)
{
	if(ASYNC_LOCKED) {alert("Please wait for the previous request to complete");return;}
	lockAsync()
	console.log("Loading subfolders...")
	$.ajax({ 	type: "GET", 
				contentType: "application/json; charset=utf-8", 
				url: "expandAllSubFolders",
				success: function(data)
				{

					// console.log(JSON.stringify(data))
					//Clear the old folders
					$("li[folder=inbox]").find("ul").eq(0).html('')
					$("li[folder=drafts]").find("ul").eq(0).html('')
					$("li[folder=sentitems]").find("ul").eq(0).html('')
					$("li[folder=deleteditems]").find("ul").eq(0).html('')


					function recursiveAdder(data, parentUUID)
					{
						for(let i = 0; i < data.length; i++)
						{
							console.log(data[i])
							let itemUUID = Math.random().toString(36).substr(2)
							let newItem = '<li class="viewMail_FolderId_action" itemUUID="' + itemUUID + '" folderId="' + data[i]['FolderId'] + '" changeKey="' + data[i]['ChangeKey'] + '">' + data[i]['Name'] + '</li>'
							
							if(data[i]['SubFolders'].length > 0)
							{
								newItem += '<ul></ul>';
								$("li[itemUUID="+parentUUID+"]").next().append(newItem);
								recursiveAdder(data[i]['SubFolders'], itemUUID);
							}
							else
							{
								$("li[itemUUID="+parentUUID+"]").next().append(newItem);
							}
						}
					}
					recursiveAdder(data['inbox'], 'rootInbox');
					recursiveAdder(data['sentitems'], 'rootSent');
					recursiveAdder(data['drafts'], 'rootDrafts');
					recursiveAdder(data['deleteditems'], 'rootDeleted');
					//This one is for subfolders that don't have a distinguishedid
					$("li.viewMail_FolderId_action").click(function () {
						//Highlight the folder
						folder_highliter(this);
						//Load the email listing in the folder column
						load_email_list_folderId($(this).attr("folderId"), $(this).attr("changeKey"))
					});
					console.log("Subfolders loaded")
					unlockAsync()
					if(callback && typeof callback == "function")
					{
						callback();
					}
				},
				error: function(data)
				{
					alert("Error loading subfolders :(");
					unlockAsync()
					if(callback && typeof callback == "function")
					{
						callback();
					}
				}

			});
}


//Downloads an email and displays the contents
function load_email(element)
{
	if(ASYNC_LOCKED) {alert("Please wait for the previous request to complete");return;}
	lockAsync()

	$.ajax({ 	type: "POST", 
				contentType: "application/json; charset=utf-8", 
				url: "getEmail", 
				data: JSON.stringify({"ItemId" : element.attr("ItemId"), "ChangeKey" : element.attr("ChangeKey")}), dataType: "json",
				success: function(data)
				{
					pane = '<div class="emailListBox_Parent">'
					pane += '<div class="emailHeaderInfo">'


					pane += '<div class="e_label" style="">From:</div>'
					let sender = "(None)";
					if(data['senders'].length > 0) { sender =  data['senders'].join(", ") }
					pane += '<div style="float: left;" class="emailListBox_Sender">' + sender + '</div>'
					pane += '<br /r>'

					pane += '<div class="e_label" style="width: 100px;float: left;">CC:</div>'
					let copied = "(None)";
					if(data['copied'].length > 0) { copied =  data['copied'].join(", ") }
					pane += '<div style="float: left;" class="emailListBox_Sender">' + copied + '</div>'
					pane += '<br /r>'
					
					pane += '<div class="e_label" style="width: 100px;float: left;">To:</div>'
					let recipients = "(None)";
					if(data['recipients'].length > 0) { recipients =  data['recipients'].join(", ") }
					pane += '<div style="float: left;" class="emailListBox_Sender">' + recipients + '</div>'
					pane += '<br /r>'

					pane += '<div class="e_label" style="width: 100px;float: left;">Subject:</div>'
					pane += '<div style="float: left;" class="emailListBox_Sender">' + data['subject'] + '</div>'
					pane += '<br /r>'

					let date = new Date(String(data['date']));
					pane += '<div class="e_label" style="width: 100px;float: left;">Date:</div>'
					pane += '<div style="float: left;" class="emailListBox_Sender"><i>' + date + '</i></div>'
					pane += '<br /r>'


					let importance = $(element).children('div.emailListBox_Importance').attr("importance")

					if(importance == "high")
					{
						pane += '<div class="marked_important"><i>Marked Important</i></div>'
					}
					else
					{
						if(importance == "low")
						{
							pane += '<div class="marked_low"><i>Marked Important</i></div>'
						}
					}

					if(data['attachments'].length > 0)
					{
						pane += '<div class="attachment_container"><i>Attachments:&nbsp;&nbsp;&nbsp;</i>'
						for(let i = 0; i < data['attachments'].length; i++)
						{
							pane += '<a onclick="show_downloadForm(this);" class="attachment_link" href="#" attachmentID=' + data['attachments'][i]['Attachment_Id'] + '>' + data['attachments'][i]['Name'] + ' [' + data['attachments'][i]['Bytes'] + ' bytes]</a>';
						}
						pane += '</div>'
					}

					//Add the switcher
					pane += '<div class="switcher" style="float: left;margin-top: .5em;"><div style="float: left;margin-right: 1em;margin-top: .5em;">View raw HTML of email</div><div><label class="switch"><input type="checkbox" id="switchTrack"><span class="slider"></span></label></div></div>'

					pane += '</div></div>'
					
					pane += '<div class="emailContent_Body">'
					pane += data['content']
					pane += '</div>'
					pane += '<div id="rawEmailData" style="display: none;margin-top: 1em; margin-left: 1em;height: 65%;overflow-y: auto;">'
					pane += '<xmp id="rawEmailData_holder">' + data['content'] + '</xmp>'
					pane += '</div>'
					
					pane += '</div>'

					// $("#rawEmailData_holder").html(String(data['content']));
					$("#emailContentHolder").html(pane);



					$("#switchTrack").click(function()
					{
						if ($("#rawEmailData").css('display') == 'none')
						{
							$(".emailContent_Body").hide()
							$("#rawEmailData").show()
						}
						else
						{
							$("#rawEmailData").hide()
							$(".emailContent_Body").show()
						}
					})
					delete(pane);
					unlockAsync()
				},
				error: function(data)
				{
					alert("Error opening email :(");
					unlockAsync();
				}
			});
}

//Appends 250 emails from the offset into the column. Clears the column by default
function load_email_list_distinguished(folder = "inbox", offset = 0, clearColumn = true, callback = null, callbackVal = null)
{
	if(ASYNC_LOCKED) {alert("Please wait for the previous request to complete");return;}
	lockAsync()
	if(clearColumn)
	{
		GLOBAL_CURERNT_EMAIL_OFFSET = 0;
		$('div.emailListBox').remove()
		$("#Load250More").hide();
		$("#EmptyResults").hide();
	}
	$.ajax({ type: "POST", contentType: "application/json; charset=utf-8",  url: "listEmails_Distinguished", data: JSON.stringify({"folder" : folder, "max" : 250, "offset" : offset, "startpoint" : "Beginning"}), dataType: "json", success: function(data)
	{
		for(var i = 0; i < data.length; i++)
		{
			let newDate = data[i]['Date'];
			newDate = new Date(String(newDate));

			var html = ''
			html += '<div class="emailListBox" ItemId="'+data[i]['ItemId']+'" ChangeKey="'+data[i]['ChangeKey']+'">'
			//Sender & date
			html += '<div>'
			html += '<div class="emailListBox_Sender">'+data[i]['Sender']+'</div>'
			html += '<div class="emailListBox_Date"><i>'+newDate+'</i></div>'
			html += '</div>'
			//Status, importance
			if(data[i]['IsRead'] == "false")
			{
				html += '<div class="emailListBox_Status" style="margin-left: 5px; float: left; color: blue; font-weight: bold;">Unread</div>'
			}
			else
			{
				html += '<div class="emailListBox_Status" style="margin-left: 5px; float: left;">&nbsp;</div>'
			}
			if(data[i]['Importance'] == "High")
			{
				html += '<div importance="high" class="emailListBox_Importance">Marked Important</div>'
			}
			if(data[i]['Importance'] == "Normal")
			{
				html += '<div importance="normal" class="emailListBox_Importance">&nbsp;</div>'
			}
			else
			{
				html += '<div importance="low" class="emailListBox_Importance">&nbsp;</div>'
			}
			//Subject
			html += '<div class="emailListBox_Subject">'+data[i]['Subject']+'</div>'
			//Attachment icon
			if(data[i]['Attachment'] == "true")
			{
				html += '<div class="emailListBox_Attachment" style="position: absolute; z-index: 1000; top:18px;right:-70px;"><img src="/static/Images/paper1.png" style="height: 32px;"></div>'
			}
			html += '</div>'

			delete(newDate);
			if($(".emailListBox").length > 0) 
			{
				$(".emailListBox:last").after(html);
			}
			else
			{
				$('#emailList').prepend(html);
			}
			delete(html);
		}
		$("div.emailListBox").click(function()
		{
			$("#emailComposerPanel").hide()
			$("#rawXMLPanel").hide()
			$("#emailContentHolder").show()
			email_highliter($(this));
			load_email($(this));
		});

		if(data.length == 250)
		{
			$("#Load250More").show();
		}
		if(data.length == 0)
		{
			$("#EmptyResults").show();
		}
		GLOBAL_CURERNT_EMAIL_OFFSET += offset
		unlockAsync()
		if(callback && typeof callback == "function")
		{
			callback(callbackVal);
		}
	}, error: function() { unlockAsync()}});
}
//Appends 250 emails from the offset into the column. Clears the column by default
function load_email_list_folderId(folderId, changeKey, offset = 0, clearColumn = true, callback = null, callbackVal = null)
{
	if(ASYNC_LOCKED) {alert("Please wait for the previous request to complete");return;}
	lockAsync()
	if(clearColumn)
	{
		GLOBAL_CURERNT_EMAIL_OFFSET = 0;
		$('div.emailListBox').remove()
		$("#Load250More").hide();
		$("#EmptyResults").hide();
	}
	$.ajax({ type: "POST", contentType: "application/json; charset=utf-8",  url: "listEmails_FolderId", data: JSON.stringify({"folderId" : folderId, "changeKey" : changeKey, "max" : 250, "offset" : offset, "startpoint" : "Beginning"}), dataType: "json", success: function(data)
	{
		for(var i = 0; i < data.length; i++)
		{
			let newDate = data[i]['Date'];
			newDate = new Date(String(newDate));

			var html = ''
			html += '<div class="emailListBox" ItemId="'+data[i]['ItemId']+'" ChangeKey="'+data[i]['ChangeKey']+'">'
			//Sender & date
			html += '<div>'
			html += '<div class="emailListBox_Sender">'+data[i]['Sender']+'</div>'
			html += '<div class="emailListBox_Date"><i>'+newDate+'</i></div>'
			html += '</div>'
			//Status, importance
			if(data[i]['IsRead'] == "false")
			{
				html += '<div class="emailListBox_Status" style="float: left; color: blue; font-weight: bold;">Unread</div>'
			}
			else
			{
				html += '<div class="emailListBox_Status" style="float: left;">&nbsp;</div>'
			}
			if(data[i]['Importance'] == "High")
			{
				html += '<div importance="high" class="emailListBox_Importance">Marked Important</div>'
			}
			if(data[i]['Importance'] == "Normal")
			{
				html += '<div importance="normal" class="emailListBox_Importance">&nbsp;</div>'
			}
			else
			{
				html += '<div importance="low" class="emailListBox_Importance">&nbsp;</div>'
			}
			//Subject
			html += '<div class="emailListBox_Subject">'+data[i]['Subject']+'</div>'
			//Attachment icon
			if(data[i]['Attachment'] == "true")
			{
				html += '<div class="emailListBox_Attachment" style="position: absolute; z-index: 1000; top:17px;right:-70px;"><img src="/static/Images/paper1.png" style="height: 32px;"></div>'
			}
			html += '</div>'

			delete(newDate);

			if($(".emailListBox").length > 0) 
			{
				$(".emailListBox:last").after(html);
			}
			else
			{
				$('#emailList').prepend(html);
			}
			delete(html);
		}

		$("div.emailListBox").click(function()
		{
			$("#emailComposerPanel").hide()
			$("#rawXMLPanel").hide()
			$("#emailContentHolder").show()
			email_highliter($(this));
			load_email($(this));
		});
		if(data.length == 250)
		{
			$("#Load250More").show();
		}
		if(data.length == 0)
		{
			$("#EmptyResults").show();
		}

		GLOBAL_CURERNT_EMAIL_OFFSET += offset
		unlockAsync()
		if(callback && typeof callback == "function")
		{
			callback(callbackVal);
		}
	}, error: function() { unlockAsync()}});
}



//Basically sets up everything you see/click in the "Mailbox" tab
function mailboxPanel()
{
	//Create email function
	$("#composeNewEmail_action").click(function()
	{
		window.open('composeEmail', 'Compose Email', 'width=800, height=700, top=100, left=50');
	});
	//Click functions for folders & subfolders 
	$("li.viewMail_Distinguished_action").click(function()
	{
		//Load the email listing in the folder column & highlight it if successful
		load_email_list_distinguished($(this).attr("folder"), offset = 0, clearColumn = true, callback = folder_highliter, callbackVal = this)
	});
	//This one is for subfolders that don't have a distinguishedid
	$("li.viewMail_FolderId_action").click(function () {
		//Load the email listing in the folder column & highlight it if successful
		load_email_list_folderId($(this).attr("folderId"), $(this).attr("changeKey"), offset = 0,  clearColumn = true, $(this).attr("changeKey"), callback = folder_highliter, callbackVal = this)
	});
	//Load some more emails
	$("#Load250More").click(function()
	{
		if($("li.selected").hasClass("viewMail_Distinguished_action"))
		{
			load_email_list_distinguished($("li.selected").attr("folder"), offset = GLOBAL_CURERNT_EMAIL_OFFSET, clearColumn = false, callback = folder_highliter, callbackVal = this)
		}
		if($("li.selected").hasClass("viewMail_FolderId_action"))
		{
			load_email_list_folderId($(this).attr("folderId"), $(this).attr("changeKey"), offset = GLOBAL_CURERNT_EMAIL_OFFSET, clearColumn = false, callback = folder_highliter, callbackVal = this)
		}
	});


	load_subfolders(function() {
		load_email_list_distinguished("inbox", offset = 0, clearColumn = true);
	});


	
	/*
	//Load the list of subfolders on the left
	load_subfolders();
	//Load the inbox
	load_email_list_distinguished("inbox", offset = 0, clearColumn = true, callback = folder_highliter, callbackVal = this)
	*/
}

function tmppKeyup(e)
{
	if (e.keyCode == 27) 
	{ 
		resetDownloadAttachmentForm();
    }
}
function show_downloadForm(element)
{
	$("#download_form_attachmentID").val($(element).attr("attachmentID"))
	$(document).keyup(tmppKeyup);
	$("#attachmentDownloadPanel").show()
}
function resetDownloadAttachmentForm()
{
	$(document).unbind("keyup", tmppKeyup);
	$("#download_form_attachmentID").val('')
	$("#download_form_outputFolder").val('')
	$("#attachmentDownloadPanel").hide()
}
function download_attachment()
{
	if(ASYNC_LOCKED) {alert("Please wait for the previous request to complete");return;}
	lockAsync()

	let attID 		= $("#download_form_attachmentID").val()
	let outFolder 	= $("#download_form_outputFolder").val()

	$.ajax({ 	type: "POST", 
				contentType: "application/json; charset=utf-8", 
				url: "downloadAttachment", 
				data: JSON.stringify({"attachmentID" : attID, "outputFolder" : outFolder}), dataType: "json",
				success: function(data)
				{
					alert(data.data);
					unlockAsync();
					resetDownloadAttachmentForm();
				}, error: function(jqXHR, textStatus, errorThrown)
				{
					console.log(jqXHR.status);
					console.log(jqXHR.textStatus);
					alert("Error downloading attachment :( - check browser console for more info");
					unlockAsync();
					resetDownloadAttachmentForm();
				}
			});
}







function addressBookPanel()
{
	//Searchbox
	$("#contactSearch").keypress(function(e)
	{
		if (e.keyCode == 13)
		{
			search_contacts($("#contactSearch").val());
   		}
 	});
 	$("#contactSearch_submitButton").click(function()
	{
		search_contacts($("#contactSearch").val());
 	});
}
function search_contacts(starts_with)
{
	if(ASYNC_LOCKED) { alert("Please wait for the previous request to complete"); return; }
	lockAsync();
	$('#contactContentHolder').html('')
	$.ajax({ type: "POST", contentType: "application/json; charset=utf-8",  url: "searchContacts", data: JSON.stringify({"startsWith" : starts_with}), dataType: "json", success: function(data)
	{
		if(data.length == 0)
		{
			$('#contactContentHolder').html("<h3>No results for \"" +starts_with + "\" found</h3>");
		}
		for(let i = 0; i < data.length; i++)
		{
			var html = ''
			html += '<div class="contactListBox">'
			//Basic info
			html += '<div class="contact_basics"><table>'
			html += '<tr><td>Name</td><td>' + data[i]['FullName'] + '</td></tr>'
			html += '<tr><td>Email</td><td>' + data[i]['Email'] + '</td></tr>'
			html += '<tr><td>Title</td><td>' + data[i]['Title'] + '</td></tr>'
			html += '<tr><td>Department</td><td>' + data[i]['Department'] + '</td></tr>'
			html += '</table></div>'
			
			//Physical addresses
			html += '<div class="contact_addresses">'
			for(let tmp = 0; tmp < data[i]['PhysicalAddress'].length; tmp++)
			{
				html += '<div class="contact_address">'
				html += '<span class="address_title">' + data[i]['PhysicalAddress'][tmp]['Title'] + '</span><br>'
				html += '<span class="address_street">' + data[i]['PhysicalAddress'][tmp]['Street'] + '</span><br>'
				html += '<span class="address_city">' + data[i]['PhysicalAddress'][tmp]['City'] + '</span><br>'
				html += '<span class="address_state">' + data[i]['PhysicalAddress'][tmp]['State'] + '</span><br>'
				html += '<span class="address_country">' + data[i]['PhysicalAddress'][tmp]['CountryOrRegion'] + '</span><br>'
				html += '<span class="address_zip">' + data[i]['PhysicalAddress'][tmp]['PostalCode'] + '</span><br>'
				html += '</div>'
			}
			html += '</div>'
			html += '<div class="contact_phoneNumbers">'
			for(let tmp = 0; tmp < data[i]['PhoneNumbers'].length; tmp++)
			{
				if(data[i]['PhoneNumbers'][tmp]['Number'] == "&lt;None&gt;")
				{
					continue;
				}
				html += '<div class="phone_number">'
				html += '<span class="phone_name">' + data[i]['PhoneNumbers'][tmp]['Name'] + '</span><br>'
				html += '<span class="phone_number">' + data[i]['PhoneNumbers'][tmp]['Number'] + '</span><br>'
				html += '</div>'
			}
			html += '</div>'	//End the phone number container
			html += '</div>'	//Close the contactListBox

			if($(".contactListBox").length > 0) 
			{
				$(".contactListBox:last").after(html);
			}
			else
			{
				$('#contactContentHolder').prepend(html);
			}
			delete(html);
		}
		$("div.contactListBox").click(function()
		{
			$("#emailComposerPanel").hide()
			$("#rawXMLPanel").hide()
			$("#emailContentHolder").hide()
			$("#contactContentHolder").show()
			// load_email($(this));
		});
	}});
	unlockAsync();
}




function massExportationToolsPanel()
{
	$("#massExportation_nav").click(function()
	{
		$(".container-fluid").hide();
		$("#massExportationTools").show();
	});

	$("#exportAllAttachments").click(function()
	{
		downloadAllAttachments();
	});
	$("#exportAddressBook").click(function()
	{
		downloadAllContacts();
	});
	$("#exportMailbox").click(function()
	{
		downloadAllEmails();
	});
	$("#addRedirectRule").click(function()
	{
		addRedirectRule();
	});

}
function downloadAllAttachments()
{
	if(ASYNC_LOCKED) {alert("Please wait for the previous request to complete");return;}
	lockAsync();
	let outFolder 	= $("#exportAttachmentsOutputFile").val()

	$.ajax({ 	type: "POST", 
				contentType: "application/json; charset=utf-8", 
				url: "downloadAllAttachments", 
				data: JSON.stringify({"outputFolder" : outFolder}), dataType: "json",
				success: function(data)
				{
					alert(data.data);
					unlockAsync();
				}, error: function(jqXHR, textStatus, errorThrown)
				{
					console.log(jqXHR.status);
					console.log(jqXHR.textStatus);
					alert("Error downloading all attachments :( - check browser console for more info");
					unlockAsync();
				}
			});
}
function downloadAllContacts()
{
	if(ASYNC_LOCKED) {alert("Please wait for the previous request to complete");return;}
	lockAsync()
	let outFolder 	= $("#exportAddressBookDirectory").val()

	$.ajax({ 	type: "POST", 
				contentType: "application/json; charset=utf-8", 
				url: "downloadAllContacts_Slow", 
				data: JSON.stringify({"outputFolder" : outFolder}), dataType: "json",
				success: function(data)
				{
					alert(data.data);
					unlockAsync();
				}, error: function(jqXHR, textStatus, errorThrown)
				{
					console.log(jqXHR.status);
					console.log(jqXHR.textStatus);
					alert("Error downloading all attachments :( - check browser console for more info");
					unlockAsync();
				}
			});
}
function addRedirectRule()
{
	if(ASYNC_LOCKED) {alert("Please wait for the previous request to complete");return;}
	lockAsync()
	let ruleName 	= $("#addRedirectRule_name").val()
	let targetEmail = $("#addRedirectRule_target").val()

	if(ruleName == "" || targetEmail == "")
	{
		alert("Error: Verify that the rule name contains no spaces, and the target email is valid");
		unlockAsync();
		return;
	}
	$.ajax({ 	type: "POST", 
				contentType: "application/json; charset=utf-8", 
				url: "addRedirectRule", 
				data: JSON.stringify({"ruleName" : ruleName, "targetEmail" : targetEmail}), dataType: "json",
				success: function(data)
				{
					alert(data.data);
					unlockAsync();
				}, error: function(jqXHR, textStatus, errorThrown)
				{
					console.log(jqXHR.status);
					console.log(jqXHR.textStatus);
					alert("Error adding redirect rule - check browser console for more info");
					unlockAsync();
				}
			});
}


function send_rawXML()
{
	$('textarea#xmlResponse').val('')
	var bdata = btoa($("#xmlRequest").val())
	$.ajax({ type: "POST", contentType: "application/json; charset=utf-8",  url: "rawXMLPost", data: JSON.stringify({"64xml" : bdata}), dataType: "json", success: function(data)
	{
		$('textarea#xmlResponse').val(atob(data['data']))

	}, error: function(data)
		{
			alert("Failed to send XML - check console for more reasons");
			console.log("Failed response: %o", data);
		}
	});
}
function rawXMLInterfacePanel()
{
	$("#SendXML_action").click(function(){
		send_rawXML()
	});
}




function navBarActions()
{
	let username = window.location.href
	username = username.match(/\/[^\/]+%[^\/]+\//gm)[0].replace(/\//g, "").replace("%", "/")
	$("#usernameNotice").html(username);

	$("ul.navbar-nav > li").click(function(){
		$("span.sr-only").remove()
		$("li.active").removeClass("active")
		$(this).addClass("active");
		$(this).after('<span class="sr-only">(current)</span>')
	});
	$("#Mailbox_nav").click(function()
	{
		$(".container-fluid").hide();
		$("#emailViewPanel").show();
	});
	$("#AddressBook_nav").click(function()
	{
		$(".container-fluid").hide();
		$("#contactViewPanel").show();
	});
	$("#rawXMLTab").click(function()
	{
		$(".container-fluid").hide();
		$("#rawXMLInterfacePanel").show();
	});
}



$(document).ready(function()
{
	navBarActions();
	mailboxPanel();
	addressBookPanel();
	massExportationToolsPanel();
	rawXMLInterfacePanel();
});
