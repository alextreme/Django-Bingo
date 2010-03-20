function load_table(placeholder, dataurl, data, refresh_rate, table_columns) {
    
    function load_data_into_table(data) {
        placeholder.find("tbody").html("");
	
	html_data = "";
	spark_data = [];
	for (var i = 0; i < data.length; i++) {
	    html_row = "<tr>";
	    data_row = data[i];

	    for (var j = 0; j < data_row.length; j++) {
		html_cell = "<td>";
		data_elm = data_row[j];
		if (data_elm == null) {
		    html_cell += 'undefined';
		}
		else if (typeof(data_elm) != 'object') { //boolean, number, string
		    html_cell += data_elm;
		}
		else { // we should have an associative array with the table column type
		    if (data_elm['type'] == 'sparkline') {
		        html_cell += "<span class='inlinesparkline'>";
		        for (var k = 0; k < data_elm['data'].length; k++) {
		            html_cell += "" + data_elm['data'][k];
			    if (k != data_elm.length - 1) {
			        html_cell += ",";
			    }
			}
		        html_cell += "</span>";
		    }
		}	
	        html_cell += "</td>";
		html_row += html_cell;
	    }
	    html_row += "</tr>";
	    html_data += html_row;
	}
	placeholder.find("tbody").append(html_data);
	$('.inlinesparkline').sparkline();
    }

    // unique timeout, otherwise this only works on the last element
    function fetch_data() {

        function on_data_received(data) {
	    load_data_into_table(data);

            if (refresh_rate != 0) {
	        setTimeout(fetch_data, refresh_rate * 1000);
	    }
         }
        
        $.ajax({
            url: dataurl,
            method: 'GET',
            dataType: 'json',
            success: on_data_received
        });
    }
    fetch_data();

}
