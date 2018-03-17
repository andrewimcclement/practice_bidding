# practice_bidding ![alt-text](https://travis-ci.org/andrewimcclement/practice_bidding.svg?branch=master) [![Coverage Status](https://coveralls.io/repos/github/andrewimcclement/practice_bidding/badge.svg?branch=master)](https://coveralls.io/github/andrewimcclement/practice_bidding?branch=master)
A short program to allow practice of new bidding systems in Bridge.

-------------------------------------------------------------------------------
__Requirements__
Python v3.6+ (f-strings are used ubiquitously).

-------------------------------------------------------------------------------
__Installation__

`git clone --recurse-submodules https://github.com/andrewimcclement/practice_bidding`
will ensure the required redeal submodule is installed at the same time.

Should you have any difficulties, please see
https://git-scm.com/book/en/v2/Git-Tools-Submodules.

-------------------------------------------------------------------------------
__Usage__:

From the command line, `python C:\path\to\practice_bidding_main.py` will use
the `XML_DEFAULT_SOURCE` constant to locate the XML file describing the bidding
system you wish to use, if you enter `default` when asked for the XML file
location. Otherwise you may enter the file location at that point.

Alternatively,
    `python C:\path\to\practice_bidding_main.py C:\path\to\system.xml`
will use the XML file located at `C:\path\to\system.xml`

You may wish to edit the `XML_DEFAULT_SOURCE` constant for your own usage.
Please do not commit these changes.

-------------------------------------------------------------------------------
__Defining the XML bidding system__:

See example_systems/chimaera.xml as an example.

&lt;bid&gt; element must always have a &lt;value&gt; element and a &lt;desc&gt;
element. For a bid to be recognised by the program, it must have a
&lt;condition&gt; element. A &lt;condition&gt; element must have a "type" tag
as either "include" or "exclude" depending on whether the hand type should be
included as a valid hand type or excluded as an invalid hand type for that bid.

An &lt;evaluation&gt; element can be added inside a &lt;condition&gt; element.
This can have various evaluation methods: &lt;hcp&gt;, &lt;points&gt; and
&lt;tricks&gt;. Note that &lt;tricks&gt; is not yet implemented.
With these elements, you can define &lt;min&gt; and &lt;max&gt; elements.

  - &lt;hcp&gt; evaluates a hand using the Milton Work Point Count if the
    attribute `hcp="standard"` is added to the root of the XML system file.
    An alternative point count `hcp="chimaera"` is defined with
    (A, K, Q, J, T) == (4.5, 3, 1.5, 0.75, 0.25)
    If neither are defined, it will fall back to the HCP function defined
    in a python file referenced by the XML system file (file location assumed
    to be in the same directory as the XML system file, referenced by addition
    of `formulas="my_evaluation_methods.py"`)

  - &lt;points&gt; is the sum of &lt;hcp&gt; and the number of cards above 4 in
    each suit.

  - &lt;tricks&gt; will be the number of playing tricks.

Multiple &lt;shape&gt; elements can be defined inside a &lt;condition&gt;
element. These must have a "type" tag, which must be one of "general", "shape",
"clubs", "diamonds", "hearts", "spades", "longer_than" or
"strictly_longer_than". A new "formula" type now supersedes "longer_than" and
"strictly_longer_than" while allowing more elaborate constructions.

  - "general" allows you to use predefined general shape constraints such as
    "balanced", "unbalanced" etc.

  - "shape" allows you to define precise shapes eg 5431 for 5 spades, 4 hearts,
    3 diamonds and 1 club, or (54)xx for 54 in the majors.

  - A suit allows you define &lt;min&gt; and &lt;max&gt; lengths for that suit
    (inclusive). Note if min > max the program will throw when parsing the
    XML file.

  - "longer_than" and "strictly_longer_than" &lt;shape&gt; elements require
    &lt;longer_suit&gt; and &lt;shorter_suit&gt; elements inside and allow you
    to define conditions such as `len(hearts) > len(spades)` for a hand.

  - "formula" &lt;shape&gt; elements allows the input of a equation in the
    lengths of the suits, e.g. `hearts + spades > diamonds + clubs`.
    +, *, - are all allowed (but not brackets). Exactly one operator of "==",
    "!=", "<=", ">=", "<", ">" must be used (replacing "<"/">" with "&[l/g]t;"
    where required).

-------------------------------------------------------------------------------
__Acknowledgements__
This would not be possible without the wonderful redeal library implemented
in Python by Antony Lee. This project uses a forked copy, but the original
can be found at https://github.com/anntzer/redeal.