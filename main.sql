# drop database ofd;

CREATE DATABASE IF NOT EXISTS ofd;

use ofd;

create table if not exists restaurants(
    id int primary key auto_increment,
    name varchar(255) not null
);

create table if not exists users (
    id int primary key auto_increment,
    username varchar(255) not null unique,
    password varchar(255) not null,
    email varchar(255) not null unique,
    phone_number varchar(255) not null unique,
    created_at timestamp default current_timestamp,
    role enum('CUSTOMER', 'CHEF', 'DELIVERY', 'ADMIN') default 'CUSTOMER',
    restaurant_id int,

    constraint fk_restaurant_chef
                    foreign key (restaurant_id)
                    references restaurants(id)
                    on delete cascade,

    constraint chk_required_restaurant_id
         check(
             (role = 'CHEF' and restaurant_id is not null) or
             (role != 'CHEF' and restaurant_id is null)
             )
);

create table if not exists addresses (
    id int primary key auto_increment,
    address varchar(255),
    user_id int not null,

    constraint fk_addresses_user
                    foreign key (user_id)
                    references users(id)
                    on delete cascade
);

create table if not exists cards (
    id int primary key auto_increment,
    user_id int not null,
    cvv int not null,
    card_number varchar(16) not null,
    card_holder_name varchar(255) not null,
    expiration_date date not null,
    type enum('VISA', 'MASTERCARD') default 'VISA',

    constraint fk_cards_user
                   foreign key (user_id)
                   references users(id)
                   on delete cascade
);

create index idx_cards_user_id on cards(user_id);

delimiter $$
create trigger before_cards_insert
before insert on cards
for each row
    begin
        if char_length(new.card_number ) != 16 and new.type = 'VISA' then
            signal sqlstate '45000'
            set message_text = 'Card number should be 16 digits';
        end if;

        if new.card_number regexp '[^0-9]' then
            signal sqlstate '45000'
            set message_text = 'Card number can only contain numbers';
        end if;
    end $$;

delimiter ;

create table if not exists wallets (
    id int primary key auto_increment,
    user_id int not null,
    balance decimal(10, 2) default 0,

   constraint fk_wallets_user
                foreign key (user_id)
                references users(id)
                on delete cascade
);

create index idx_wallets_user_id on wallets(user_id);

create table if not exists orders (
    id int primary key auto_increment,
    user_id int not null,
    chef_id int,
    address_id int not null,
    price decimal(10, 2) not null,
    payment_method enum('CARD', 'CASH') not null,
    wallet_id int,
    created_at timestamp default current_timestamp,
    status enum('PENDING', 'CONFIRMED', 'DELIVERED', 'CANCELLED') default 'PENDING',

    constraint fk_orders_user
                    foreign key (user_id)
                    references users(id)
                    on delete cascade,

    constraint fk_orders_chef
                    foreign key (chef_id)
                    references users(id),

    constraint fk_orders_wallet
                    foreign key (wallet_id)
                    references wallets(id),

    constraint fk_orders_address
                    foreign key (address_id)
                    references addresses(id),

    constraint chk_payment_method
        check (
            (payment_method = 'CASH' AND wallet_id IS NULL) OR
            (payment_method = 'CARD' AND wallet_id IS NOT NULL)
            ),

    constraint chk_chef_required
        check (
            (status IN ('PENDING', 'CANCELLED') and chef_id is null) or
            (status IN ('CONFIRMED', 'DELIVERED') and chef_id is not null)
            )
);

delimiter $$
create trigger before_chef_delete
    before delete on users
    for each row
begin
    declare new_chef_id int;
    if(old.role = 'CHEF') then
        select id into new_chef_id
        from users
        where role = 'CHEF'
          and restaurant_id = old.restaurant_id
          and id != old.id
        limit 1;

        if(new_chef_id is not null) then
            update orders
            set chef_id = new_chef_id
            where chef_id = old.id;
        else
            update orders set status = 'CANCELLED', chef_id = null where chef_id = old.id;
        end if;
    end if;
end $$
delimiter ;

create index idx_orders_user_id on orders(user_id);
create index idx_orders_wallet_id on orders(wallet_id);
create index idx_orders_address_id on orders(address_id);
create index idx_orders_chef_id on orders(chef_id);

create table if not exists food(
    id int primary key auto_increment,
    name varchar(255) not null,
    price decimal(10, 2) not null,
    restaurant_id int not null,

    constraint fk_restaurant_food
                   foreign key (restaurant_id)
                   references restaurants(id)
                   on delete cascade
);

create index idx_food_restaurant_id on food(restaurant_id);
