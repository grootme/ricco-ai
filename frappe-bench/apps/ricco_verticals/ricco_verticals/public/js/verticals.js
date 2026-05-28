// RICCO Verticals - Main JavaScript
frappe.provide('ricco_verticals');

ricco_verticals = {
	// Restaurant Module
	restaurant: {
		get_available_tables: function(date, time, party_size) {
			return frappe.call({
				method: 'ricco_verticals.restaurant.api.get_available_tables',
				args: {
					date: date,
					time: time,
					party_size: party_size
				}
			});
		},
		
		check_table_availability: function(table, date, time) {
			return frappe.call({
				method: 'ricco_verticals.restaurant.api.check_table_availability',
				args: {
					table: table,
					date: date,
					time: time
				}
			});
		}
	},
	
	// Gym Module
	gym: {
		check_membership: function(member) {
			return frappe.call({
				method: 'ricco_verticals.gym.api.check_membership_status',
				args: {
					member: member
				}
			});
		},
		
		record_attendance: function(member) {
			return frappe.call({
				method: 'ricco_verticals.gym.api.record_attendance',
				args: {
					member: member
				}
			});
		}
	},
	
	// Real Estate Module
	realestate: {
		get_property_availability: function(property) {
			return frappe.call({
				method: 'ricco_verticals.realestate.api.get_property_availability',
				args: {
					property: property
				}
			});
		}
	},
	
	// Healthcare Module
	healthcare: {
		check_appointment_availability: function(practitioner, date, time) {
			return frappe.call({
				method: 'ricco_verticals.healthcare.api.check_appointment_availability',
				args: {
					practitioner: practitioner,
					date: date,
					time: time
				}
			});
		}
	},
	
	// Hotel Module
	hotel: {
		search_rooms: function(check_in, check_out, guests, room_type) {
			return frappe.call({
				method: 'ricco_verticals.hotel.api.search_available_rooms',
				args: {
					check_in: check_in,
					check_out: check_out,
					guests: guests,
					room_type: room_type
				}
			});
		},
		
		quick_checkin: function(booking) {
			return frappe.call({
				method: 'ricco_verticals.hotel.api.quick_checkin',
				args: {
					booking: booking
				}
			});
		},
		
		quick_checkout: function(checkin) {
			return frappe.call({
				method: 'ricco_verticals.hotel.api.quick_checkout',
				args: {
					checkin: checkin
				}
			});
		}
	}
};

// Common utilities
ricco_verticals.utils = {
	format_currency: function(amount, currency) {
		return format_currency(amount, currency || frappe.boot.sysdefaults.currency);
	},
	
	format_date: function(date) {
		return frappe.datetime.str_to_user(date);
	},
	
	show_alert: function(message, type) {
		frappe.show_alert({
			message: message,
			indicator: type || 'blue'
		});
	}
};
