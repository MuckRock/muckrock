import $ from "jquery";
// jQuery UI modules attach to the global jQuery and do not import their own
// dependencies, so the global and each dependency must load first.
import "./jquery-global";
import "jquery-ui/ui/version";
import "jquery-ui/ui/keycode";
import "jquery-ui/ui/widgets/datepicker";

export const presets = {
  // Date-range filters on list pages and the FOIA log upload form.
  ".datepicker": {
    changeMonth: true,
    changeYear: true,
    minDate: new Date(2010, 0, 1),
    maxDate: "+1y",
    yearRange: "2010:+1",
  },
  ".datepicker-future": {
    changeMonth: true,
    changeYear: true,
    minDate: 0,
    maxDate: "+1y",
  },
  ".datepicker-simple": {
    changeMonth: true,
    changeYear: true,
  },
};

// FOIAEmbargoForm rejects dates more than 30 days out.
export const embargoOptions = {
  maxDate: "+30d",
  minDate: 0,
  firstDay: 1,
  numberOfMonths: 1,
};

export const estimateOptions = {
  changeMonth: true,
  changeYear: true,
  dateFormat: "yy-mm-dd",
  minDate: 0,
};

/**
 * Attach date pickers to every matching input under `root`.
 *
 * The request-detail pickers go first: a second `.datepicker()` call on an
 * input is ignored, so the embargo input would otherwise get the filter preset.
 */
export function initDatepickers(root = document) {
  const $root = $(root);

  const $embargoForm = $root.find("#embargo-form");
  const defaultDate = $embargoForm.data("defaultDate");
  $embargoForm
    .find(".datepicker")
    .datepicker(
      defaultDate ? { ...embargoOptions, defaultDate } : embargoOptions,
    );

  $root.find("form.change-date #id_date_estimate").datepicker(estimateOptions);

  for (const [selector, options] of Object.entries(presets)) {
    $root.find(selector).datepicker(options);
  }
}
