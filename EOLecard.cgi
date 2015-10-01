#!/usr/bin/perl -w
use CGI  qw(-utf8);
use URI::Escape;
use HTML::Entities;
use LWP::Simple;
use JSON -support_by_pp;
use Try::Tiny;
use utf8; 

$q = CGI->new;
print $q->header;

my $to = $q->param('mailto');
my $mesg = $q->param('m');
my $recipient_name = $q->param('r');
my $data_objID = defined($q->param('i'))?int($q->param('i')):undef;
my $pageID = defined($q->param('p'))?int($q->param('p')):undef;
my $card_style = int($q->param('s')||0);

sub ROT13_plus {
    #do equivalent of rot13, also switch spaces & underscores / commas & tildas, since spaces & commas are most likely in messages
    #only do for strict ascii chars A-Z and a-z. Others can be left
    $_ = shift;
    tr/abcdefghijklmnopqrstuvwxyz/nopqrstuvwxyzabcdefghijklm/;
    tr/ABCDEFGHIJKLMNOPQRSTUVWXYZ/NOPQRSTUVWXYZABCDEFGHIJKLM/;
    tr/ ,_~/_~ ,/;
    return $_;
}

sub get_img_src {
    my $dID = shift;
    my $url = "http://eol.org/api/data_objects/1.0/$dID.json?cache_ttl=100000"; #see http://eol.org/api/docs/data_objects
    my $j=3;
    my $pg;
    while (not($pg = fetch_json_page($url))) {
    	last unless ($j--); #try getting the page a few times
	    sleep(1); #wait a bit and try again
	};
	if (!($pg->{dataObjects}) || 0==@{$pg->{dataObjects}}) {
        return undef;
    } else {
        return $pg->{dataObjects}->[0]->{"eolMediaURL"};
    }
}

sub list_media_pages {
	my $id = shift;
	return unless ($id =~ /^\d+$/);
	my $pagebase = "http://eol.org/api/pages/1.0/"; #see http://eol.org/api/docs/pages
	my %page_params = (
	  	images=>75,
  		videos=>0,
  		sounds=>0,
  		maps=>0,
  		page=>1,
  		text=>0,
  		subjects=> '',
  		details=>'true',
  		licenses=>'pd|cc-by',
  		vetted=>'1'
	);

	my $url = $pagebase.$id.".json?".join("&", map{"$_=$page_params{$_}"} keys %page_params);
	my $j=0;
	while (not($pg = fetch_json_page($url))) {
    	last unless $j--; #try getting the page a few times
	    sleep(1); #wait a bit and try again
	};

    $q->start_html();
	unless ($pg) {
    	print "Error in getting json page result from EoL for page id $id, tried $j times<br>";
	} else {
	    print "<div id='results'>";
		if (!($pg->{dataObjects}) || 0==@{$pg->{dataObjects}}) {
    		print "<h1>No appropriate data objects found in EoL for the following page:</h1>";
    		print "<code>ID:</code> $id<br><code>Scientific name:</code> $pg->{scientificName}";
    	} else {
			print "<h2>Select the image for your card</h2>";
	  		foreach my $obj (@{$pg->{dataObjects}}) {
	  		   if ($dID = $obj->{dataObjectVersionID}) {
	  		       my $title = uri_escape_utf8($obj->{title} || '');
    	  		   print "<a href='";
    	  		   print $q->url()."?i=$dID'>";
	         		if ($obj->{eolThumbnailURL}) {
	          			print "<img src='$obj->{eolThumbnailURL}' alt='$title' title='$title'>";
		            } elsif ($title) {
					    print "<div>$title</div>"
		            }
		            print "</a>";
	  		   }
		  };
		}
	};
    $q->end_html();
}

unless (defined $data_objID) {
    #this is the basic page - pick an image to use from the highest rated PD/CC-BY images
    unless (defined $pageID) {
        print $q->start_html(-title=>'Select your area of interest');
        print 'Select an area:<form action=""><select name="p">
  <option value="1" selected="selected">all animals</option>
  <option value="7674">cats</option>
  <option value="7662">carnivores</option>
  <option value="7649">whales & dolphins</option>
  <option value="281">all plants (buggy!)</option>
  <option value="282">flowering plants plants</option>
  <option value="8156">orchids</option>
  </select>
  <input type="submit" name="Find pictures">
  </form>';
         print $q->end_html();
    } else {
        #display the top 75 PD or CC-BY images
        list_media_pages($pageID);  
    }
} elsif (defined $to) {
    
    #this creates the mailto link, which can be sent. Any ASCII characters in the message are in simple ROT13 to make it less obvious to the recipient
    
    my $url = $q->url()."?i=$data_objID&s=$card_style";
    #strip html tags
    print $q->start_html(-title=>'Ecard');
    if ($mesg) {
        $mesg =~ s/[><]//g; #strip any html, to avoid malicious stuff passed into the email
        $url.= "&m=".uri_escape_utf8(ROT13_plus($mesg));
    } else {
        $url.= "&m=";
    }        
    if ($recipient_name) {
        $recipient_name =~ s/[><]//g; #strip any html, to avoid malicious stuff
        $url.="&r=".uri_escape_utf8(ROT13_plus($recipient_name));
    }
    print 'Your card is ready. <a href="mailto:';
    print uri_escape_utf8($to);
    print '?subject=';
    print uri_escape_utf8(qq|An ecard for you|);
    print '&body=';
    print uri_escape_utf8(qq|I've just sent you an ecard from the Encyclopedia of Life.\nGo to <$url> to see it|);
    print '">Click here</a> to open a new email with the link to your card included. Then simply send it.';
    print $q->end_html;
    
} elsif (defined $mesg) {
    #only show a card if there is a message
    #this is the ecard which is displayed. The message is converted back from ROT13
    my $src = get_img_src($data_objID);
    unless ($src) {
        print $q->start_html(-title=>'EoL error');
    	print "<h1>Sorry, there is something wrong with your ecard</h1>";
    	print "Perhaps the Encyclopedia of Life is not accessible at the moment?";
    	print "Please try again later";
        print $q->end_html;
    } else {
        $src =~ s/_orig.jpg$/_580_360.jpg/;
        $title = 'An EoL ecard';
        $title .= " for ".ROT13_plus($recipient_name) if defined $recipient_name;
        print $q->start_html(-title=>$title);
        print "<img src = '$src'><br />";
        print encode_entities(ROT13_plus($mesg)) if defined $mesg;
        print $q->end_html;
    }
} else {
    my $src = get_img_src($data_objID);
    unless ($src) {
        print $q->start_html(-title=>'EoL error');
    	print "<h1>Sorry, we could not find the required image</h1>";
    	print "Perhaps the Encyclopedia of Life is not accessible at the moment?";
    	print "Please try again later";
        print $q->end_html;
    } else {
        $src =~ s/_orig.jpg$/_580_360.jpg/;
    	print $q->start_html(-title=>'Construct a card');
        print "<div id='header'><a href='http://eol.org'><img src='http://eol.org/assets/v2/logo-f69b42438cbe43f0eadf60243e0fd8be.png' /></a>
        <p>This is a simple test to see if you can use mailto links to create ecards</p>
<img src='$src' /><br />
<form action='' accept-charset='utf-8'>
Recipient name: <input type='text' name='r' id='r'><br />
Recipient email: <input type='email' name='mailto' id='mailto'><br />
Message: <textarea name='m' id='m'></textarea>
<input type='hidden' name='i' value='$data_objID'>
Card style
<select name='style'>
<option value='0' selected='selected'>normal</option>
<option value='1'>fancy</option>
<option value='2'>etc</option>
</select><br />
<input type='submit' name='Construct card'>
</form>
</div>";
	print $q->end_html();
    }
}

sub fetch_json_page
{
  my $json = new JSON;
  my ($json_url) = shift;
  # download the json page:
  my $json_text;
  my $content = get( $json_url );
  try {
    # these are some nice json options to relax restrictions a bit:
    $json_text=$json->allow_nonref->utf8->relaxed->escape_slash->loose->allow_singlequote->allow_barekey->decode($content);
  } catch {
    warn "Caught JSON error: $_\n";
  };
  return $json_text;
}
