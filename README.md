# practice-bidding
A short program to allow practice of new bidding systems in Bridge.

-------------------------------------------------------------------------------
Usage:
From the command line, "python C:\path\to\robot_bidding.py" will use the
XML_DEFAULT_SOURCE constant to locate the XML file describing the bidding
system you wish to use, if you enter "default" when asked for the XML file
location. Otherwise you may enter the file location at that point.

Alternatively, "python C:\path\to\robot_bidding.py C:\path\to\system.xml"
will use the XML file located at "C:\path\to\system.xml"

You may wish to edit the XML_DEFAULT_SOURCE constant for your own usage.
Please do not commit these changes.
If you refactor it, please create a .bat file for me to use as a replacement.

-------------------------------------------------------------------------------
Defining the XML bidding system:
See chimaera.xml as an example.

&lt;bid&gt; element must always have a &lt;value&gt; element and a &lt;desc&gt;
element. For a bid to be recognised by the program, it must have a <condition>
element. A &lt;condition&gt; element must have a "type" tag as either "include"
or "exclude" depending on whether the hand type should be included as a valid
hand type or excluded as an invalid hand type for that bid.

An &lt;evaluation&gt; element can be added inside a &lt;condition&lt; element.
This can have various evaluation methods: &lt;hcp&gt;, &lt;points&gt; and
&lt;tricks&gt;. Note that &lt;tricks&gt; is not yet implemented.
With these elements, you can define &lt;min&gt; and &lt;max&gt; elements.

  - <hcp> evaluates a hand using (A, K, Q, J, T) = (4.5, 3, 1.5, 0.75, 0.25)
    This can be changed in the __init__ method of BiddingProgram.

  - <points> is the sum of <hcp> and the number of cards above 4 in each suit.

  - <tricks> will be the number of playing tricks.

Multiple &lt;shape&gt; elements can be defined inside a &lt;condition&gt; element. These
must have a "type" tag, which must be one of "general", "shape", "clubs",
"diamonds", "hearts", "spades", "longer_than" or "strictly_longer_than".

  - "general" allows you to use predefined general shape constraints such as
    "balanced", "unbalanced" etc.

  - "shape" allows you to define precise shapes eg 5431 for 5 spades, 4 hearts,
    3 diamonds and 1 club, or (54)xx for 54 in the majors.

  - A suit allows you define <min> and <max> lengths for that suit (inclusive).

  - <longer_than> and <strictly_longer_than> elements require <longer_suit>
    and <shorter_suit> elements inside and allow you to define conditions such
    as len(hearts) > len(spades) for a hand.