$(function() {
  $("input[name=delete]").on("click", function () {
    if (!confirm("Are you sure you want to delete?\n"
                 + "This action cannot be reversed.")) {
      return false;
    }
  });

  // TODO validate!
  var problemList = $("#problems");
  reunmberProblemsList = function (removeEmpty) {
    var i = 0;
    problemList.find("li").each(function () {
      var $this = $(this);
      nameInput = $this.find("input[name$='problem_name']")
      scoreInput = $this.find("input[name$='score']")
      removeEmpty = false;
      if (removeEmpty && (nameInput.val() == '' || scoreInput.val == '')) {
        $this.remove();
      }
      nameInput
        .attr("id", "problems-" + i + "-problem_name")
        .attr("name", "problems-" + i + "-problem_name");
      scoreInput
        .attr("id", "problems-" + i + "-score")
        .attr("name", "problems-" + i + "-score");
      i++;
    });

    if (problemList.find("input").length > 0) {
      $("#max_score").parent("li").hide();
      problemList.parent("li").show();
    } else {
      $("#max_score").parent("li").show();
      problemList.parent("li").hide();
    }
  }

  var removeLink = $("<a class='remove' href='javascript:void(0)'>(x)</a>");
  problemList.find("li:has(input)").append(removeLink);

  var addProblemRow = problemList.find("li:last-child");
  addProblemRow.remove();

  var addProblemLink = $("<li><a href='javascript:void(0)'>(Add New Problem)</a></li>");
  problemList.append(addProblemLink);
  addProblemLink.on("click", function () {
    var problemCount = problemList.find("li").length - 1;
    var newRow = addProblemRow.clone().show();

    newRow.insertBefore(addProblemLink);
    reunmberProblemsList(false);
  });

  problemList.on("click", "a.remove", function () {
    $(this).parent("li").remove();
    reunmberProblemsList(false);
  });

  $(".use_problems").on("click", function () {
    $(this).parent("li").hide();
    problemList.parent("li").show();
    addProblemLink.trigger("click");
  });

  reunmberProblemsList(true);

  $(".new_test_file_submit").on("click", function () {
    var container = $(this).parent();
    var file = container.find("input[name=test_file]");
    var tester = container.find("select[name=tester]");
    var timeout = container.find("input[name=timeout]")
    var required_files = container.find("textarea[name=required_files]");

    if (file.val() == "") {
      alert("No test file was selected.");
      return;
    }

    var formData = new FormData();
    formData.append('tester', tester.val());
    formData.append('required_files', required_files.val());
    formData.append('timeout', timeout.val());
    formData.append('test_file', file.get(0).files[0]);

    $.ajax({
      url: 'testfile/',
      type: 'PUT',
      data: formData,
      processData: false,
      contentType: false,
      success: function(data) {
        make_testfile_entry(data);
      }
    });
  });

  var testFilesList = $(".testfiles_list fieldset ul");

  testFilesList.on("change", ".testfile .edit_all :input", function () {
    var $this = $(this);
    var inputs = $this.closest("ol").find("[name='" + $this.attr("name") + "']");
    if ($this.is(":checkbox,:radio")) {
      inputs.prop("checked", $this.prop("checked"));
    } else {
      inputs.val($this.val());
    }
  });

  testFilesList.on("click", ".test_file_submit", function () {
    var testFile = $(this).closest(".testfile");
    var data = testFile.data("json");
    data.required_files = testFile.find("textarea[name='required_files']").val().split("\n");
    data.timeout = testFile.find("input[name=timeout]").val();
    testFile.find(".unittests .unittest:not(.edit_all)").each(function (i, e) {
      var testData = _(data.unittests).find(function(u) {
        return u.id == $(e).data("json").id;
      });
      for (var property in testData) {
        if (testData.hasOwnProperty(property)) {
          var input = $(e).find(":input[name='" + property + "']");
          if (input.length === 0) {
            continue;
          }
          if (input.is(":checkbox,:radio")) {
            testData[property] = input.prop("checked");
          } else {
            testData[property] = input.val();
          }
        }
      }
    });

    $.ajax({
      url: 'testfile/' + data.id + '/',
      type: 'POST',
      data: JSON.stringify(data),
      dataType: "json",
      contentType: "application/json; charset=utf-8"
    });
  });

  testFilesList.on("click", ".test_file_delete", function () {
    var testFile = $(this).closest(".testfile");
    var data = testFile.data("json");
    if (!confirm("Are you sure you want to delete test " + data.filename + "?")) {
      return;
    }
    $.ajax({
      url: 'testfile/' + data.id + '/',
      type: 'DELETE',
      success: function() {
        testFile.remove();
      }
    });
  });

  var sampleTestFile = $(".testfiles_list .hidden li.testfile").clone();
  // TODO show issues with individual unittests (such as invalid problem)
  function make_testfile_entry(testfile) {
    var newTestFile = sampleTestFile.clone();
    newTestFile.data("json", testfile);
    newTestFile.find("span[name='testfile_name']").text(testfile.filename);
    newTestFile.find("span[name='tester']").text(testfile.tester);
    newTestFile.find("input[name='timeout']").val(testfile.timeout);
    newTestFile.find("textarea[name='required_files']").val(testfile.required_files.join("\n"));
    var unitTestList = newTestFile.find(".unittests");
    var editAllRow = unitTestList.find("li.unittest.edit_all");
    testfile.unittests.forEach(function (unittest) {
      var row = editAllRow.clone();
      row.data("json", unittest);
      row.removeClass("edit_all");
      row.find(".edit_all_label").remove();
      row.find(".hidden").removeClass("hidden");
      for (var property in unittest) {
        if (unittest.hasOwnProperty(property)) {
          var input = row.find(":input[name='" + property + "']");
          if (input.is(":checkbox,:radio")) {
            input.prop("checked", unittest[property]);
          } else {
            input.val(unittest[property]);
          }
        }
      }
      unitTestList.append(row);
    });
    editAllRow.find(".hidden").remove();
    testFilesList.append(newTestFile);
  }

  if (typeof testfiles !== "undefined") {
    testfiles.forEach(function (testfile) {
      make_testfile_entry(testfile);
    });
  }
});
