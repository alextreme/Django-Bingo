function load_table(placeholder, dataurl, refresh_rate, element_id) {
    
    function load_data_into_table(data) {
        placeholder.find("tbody").html("");
	
	html_data = "";
	inline_data = [];

	for (var i = 0; i < data.length; i++) {
	    html_row = "<tr>";
	    data_row = data[i];

	    for (var j = 0; j < data_row.length; j++) {
		html_cell = "<td>";
		data_elm = data_row[j];

		// Load the data element in the correct format (depends on the column type)
		if (data_elm == null) {
		    html_cell += 'undefined';
		}
		else if (typeof(data_elm) != 'object') { //boolean, number, string
		    html_cell += data_elm; // Shouldn't be used anymore
		}
		else { // we should have an associative array with the table column type
		    if (data_elm['type'] == 'text') {
                    	// Add threshold-indicators (if they have been specified)
		    	if (data_elm['thresholds'] != null) {
			    data_value = parseFloat(data_elm['data']); // Avoid comparing int/float as a string

			    for (var k = 0; k < data_elm['thresholds'].length; k++) {
			    	valid = false;
			    	threshold = data_elm['thresholds'][k]
			    	if (threshold['from'] != null && threshold['to'] != null) {
				    if (data_value > threshold['from'] && data_elm['data'] < threshold['to']) { valid = true; }
				}
			    	else if (threshold['from'] == null && threshold['to'] != null) {
				    if (data_value < threshold['to']) { valid = true; }
				}
			    	else if (threshold['from'] != null && threshold['to'] == null) {
				    if (data_value > threshold['from']) { valid = true; }
				}
				if (valid && threshold['level'] == 1) {
				    html_cell += "<img class='threshold' src='/media/dashboard/level-1.png' />";
				}
				if (valid && threshold['level'] == 2) {
				    html_cell += "<img class='threshold' src='/media/dashboard/level-2.png' />";
				}
			    }
			}

			html_cell += data_elm['data']; // Strings, date/time, decimals and integers
		    }
		    else if (data_elm['type'] != '') {
		        html_cell += "<span id='inline_element-" + element_id + "-" + inline_data.length + "'>Loading...</span>";
			inline_data_row = [];
		        for (var k = 0; k < data_elm['data'].length; k++) {
		            inline_data_row.push(data_elm['data'][k]);
			}
                    	// Add threshold-indicators (if they have been specified)
			threshold_values = null;
		    	if (data_elm['thresholds'] != null) {
			    for (var k = 0; k < data_elm['thresholds'].length; k++) {
			    	valid = false;
			    	threshold = data_elm['thresholds'][k]
				if (threshold['level'] != 0) { continue; } // only use green threshold
				threshold_values = threshold;
			    }
			}
			inline_data.push(Array(data_elm['type'], inline_data_row, threshold_values));
		    }
		}	
	        html_cell += "</td>";
		html_row += html_cell;
	    }
	    html_row += "</tr>";
	    html_data += html_row;
	}
	placeholder.find("tbody").append(html_data);

	// Enable all the embedded elements in this table

	for (var i = 0; i < inline_data.length; i++) {
	    options = {type: inline_data[i][0], 'width': "100%"};
	    if (inline_data[i][2] != null && inline_data[i][0] == 'line') { // threshold values
	        if (inline_data[i][2]['from'] != null) { options['normalRangeMin'] = inline_data[i][2]['from']; }
		if (inline_data[i][2]['to'] != null) { options['normalRangeMax'] = inline_data[i][2]['to']; }
		if (options['normalRangeMin'] == null) { options['normalRangeMin'] = 0; }
		if (options['normalRangeMax'] == null) { options['normalRangeMax'] = 9999; }
		options['normalRangeColor'] = "#99ff99"; // not specified in jquery sparklines docs
		options['fillColor'] = false;
	    }
	    $('#inline_element-' + element_id + '-' + i).sparkline(inline_data[i][1], options);
	}
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
