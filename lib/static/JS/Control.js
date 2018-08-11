//Checks with the server and loads the table up with the popped users

function refreshTable()
{
	$("tbody tr").remove();
	$.ajax({url: "/listSessions", success: function(data)
	{
		var html = '';
		for(var i = 0; i < data.Users.length; i++)
		{
			html += '<tr><td>' + data.Users[i] + '</td><td><a target="_blank" href="/EWStoOWA/' + data.Users[i].replace("/", "%") + '/">Go to Portal</a></td></tr>';
		}
		$('tbody').append(html);
	}});
}
$(document).ready(function(){
	refreshTable();
	setInterval(refreshTable, 8000);
});